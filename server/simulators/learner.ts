/* eslint-disable no-delete-var */
/* eslint-disable no-param-reassign */
/* eslint-disable no-loop-func */
/* eslint-disable prefer-arrow-callback */
/* eslint-disable no-console */
/* eslint-disable semi */
/* eslint-disable no-await-in-loop */
/* eslint-disable radix */
/* eslint-disable no-plusplus */
/* eslint-disable no-restricted-syntax */
/* eslint-disable guard-for-in */
/* eslint-disable max-len */
/* eslint-disable camelcase */
import axios from 'axios'
import { pick } from 'lodash'
import csv from 'csv-parser'
import fs, { PathLike } from 'fs'

function buildFeedbackMap(data: any, feedback: any, header: any): any {
    const feedbackMap: any = {};
    const rows = Object.keys(data);
    const cols = header;
    for (let i = 0; i < rows.length; i++) {
        const tup: any = {};
        for (let j = 0; j < cols.length; j++) {
            const cell = feedback.find((e: any) => {
                const trimmedCol = cols[j].replace(/[\n\r]+/g, '');
                return e.row === parseInt(data[rows[i]].id) && e.col === trimmedCol;
            });
            tup[cols[j]] = cell.marked;
        }
        feedbackMap[rows[i]] = tup;
    }
    return feedbackMap;
}

async function run(s: number) {
    let master_data_fp: PathLike
    if (s === 0) {
        master_data_fp = '../data/toy.csv'
    } else if (s % 4 === 1) {
        master_data_fp = '../data/airport_1.csv'
    } else if (s % 4 === 2) {
        master_data_fp = '../data/airport_2.csv'
    } else if (s % 4 === 3) {
        master_data_fp = '../data/omdb_3.csv'
    } else if (s % 4 === 0) {
        master_data_fp = '../data/omdb_4.csv'
    } else {
        console.error('there was a problem determining the master data filepath. defaulting to example scenario')
        master_data_fp = '../data/dirty_toy.csv'
    }

    console.log(s.toString())
    console.log(master_data_fp)

    let header
    let project_id
    try {
        const response = await axios.post('http://localhost:5000/duo/api/import', { scenario_id: s.toString() })
        const res = JSON.parse(response.data)
        header = res.header
        project_id = res.project_id
    } catch (err) {
        console.error(err)
        header = null
        project_id = null
    }
    console.log(project_id)

    let data: any
    let feedback: any
    try {
        console.log('before sample')
        const response = await axios.post('http://localhost:5000/duo/api/sample', { project_id });
        console.log('after sample')
        const res = JSON.parse(response.data);
        const { sample } = pick(res, ['sample']);
        feedback = JSON.parse(res.feedback)
        data = Object.values(JSON.parse(sample));
        console.log('parsed data')
        for (const i in data) {
            const row: any = data[i]
            for (const j in row) {
                if (j === 'id') break;

                if (row[j] == null) row[j] = '';
                else if (typeof row[j] !== 'string') row[j] = row[j].toString();
                if (!Number.isNaN(row[j]) && Math.ceil(parseFloat(row[j])) - parseFloat(row[j]) === 0) {
                    row[j] = Math.ceil(row[j]).toString();
                }
            }
        }
        console.log('prepped data')
    } catch (err) {
        console.error(err);
    }

    const master_data: any = []
    const readFile = (file: PathLike): Promise<void> => new Promise((resolve, reject) => {
        fs.createReadStream(file)
            .pipe(csv())
            .on('data', (d) => {
                // console.log(d)
                master_data.push(d)
            })
            .on('end', () => {
                console.log('read csv at '.concat(file.toString()));
                resolve()
            });
    })

    await readFile(master_data_fp)

    console.log('got master data')
    let msg = '';

    console.log('initialized feedback object')

    let threshold: number = 0.3
    while (msg !== '[DONE]') {
        const feedbackMap = buildFeedbackMap(data, feedback, header);

        /* Learner behavior */
        for (const i in data) {
            const sample_row = Object.keys(data[i]).reduce((filtered: any, key: string) => {
                if (key !== 'id') {
                    if (typeof (data[i][key]) === 'number') filtered[key] = data[i][key].toString()
                    else filtered[key] = data[i][key]
                }
                return filtered
            }, {})
            if (JSON.stringify(sample_row) === JSON.stringify(master_data[data[i].id])) {
                for (let j = 0; j < header.length; j++) {
                    const decision: number = Math.random()
                    if (decision > threshold) { // Anti-oracle
                        const d = Math.floor(Math.random() * header.length)
                        if (d === j) {
                            feedbackMap[i][header[j]] = true
                        }
                    }
                }
            } else {
                for (let j = 0; j < header.length; j++) {
                    const decision: number = Math.random()
                    if (decision <= threshold) { // Oracle
                        if (sample_row[header[j]] !== master_data[data[i].id][header[j]]) {
                            feedbackMap[i][header[j]] = true;
                        }
                    }
                }
            }
        }

        // console.log(numMarkedTuples)
        // console.log(numMarkedCells)

        feedback = {};
        for (const f in feedbackMap) {
            feedback[data[f].id] = feedbackMap[f];
        }
        let is_new_feedback = false;
        for (const idx in feedback) {
            for (const col in feedback[idx]) {
                if (feedback[idx][col] === true) {
                    is_new_feedback = true;
                    break;
                }
            }
            if (is_new_feedback) break;
        }

        const formData = {
            project_id,
            feedback,
            refresh: 0,
            is_new_feedback: (is_new_feedback === true ? 1 : 0),
        }

        try {
            const response = await axios.post('http://localhost:5000/duo/api/clean', formData);
            const res = JSON.parse(response.data);
            msg = res.msg;
            if (msg !== '[DONE]') {
                const { sample } = pick(res, ['sample']);
                feedback = JSON.parse(res.feedback);
                data = Object.values(JSON.parse(sample));

                for (const i in data) {
                    const row: any = data[i]
                    for (const j in row) {
                        if (j === 'id') break;

                        if (row[j] == null) row[j] = '';
                        else if (typeof row[j] !== 'string') {
                            row[j] = row[j].toString();
                            if (j === 'zip') {
                                while (row[j].length < 5) {
                                    row[j] = '0'.concat(row[j])
                                }
                            }
                        }
                        if (!Number.isNaN(row[j]) && Math.ceil(parseFloat(row[j])) - parseFloat(row[j]) === 0) {
                            row[j] = Math.ceil(row[j]).toString();
                        }
                    }
                }
                if (threshold < 0.9) {
                    threshold += 0.1
                }
            }
        } catch (err) {
            console.error(err);
            msg = '[DONE]';
        }
    }
}

const s = parseInt(process.argv[2])
run(s)
