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
import { harmonic } from 'array-means'
import * as scenarios from './scenarios.json'

interface Hypothesis {
    cfd: string,
    score: number,
    conf: number,
    support: number[],
    vios: number[],
    vio_pairs: number[][],
}

interface FD {
    fd: string,
    lhs: string[],
    rhs: string[],
    curr_p: number
    p_history: number[],
    support: number[],
    vios: number[]
}

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
    let full_dirty_data_fp: PathLike
    if (s === 0) {
        master_data_fp = '../data/toy.csv'
        full_dirty_data_fp = '../data/dirty_toy.csv'
    } else if (s % 4 === 1) {
        master_data_fp = '../data/airport_1.csv'
        full_dirty_data_fp = '../data/dirty_airport_1.csv'
    } else if (s % 4 === 2) {
        master_data_fp = '../data/airport_2.csv'
        full_dirty_data_fp = '../data/dirty_airport_2.csv'
    } else if (s % 4 === 3) {
        master_data_fp = '../data/omdb_3.csv'
        full_dirty_data_fp = '../data/dirty_omdb_3.csv'
    } else if (s % 4 === 0) {
        master_data_fp = '../data/omdb_4.csv'
        full_dirty_data_fp = '../data/dirty_omdb_4.csv'
    } else {
        console.error('there was a problem determining the master data filepath. defaulting to example scenario')
        master_data_fp = '../data/toy.csv'
        full_dirty_data_fp = '../data/dirty_toy.csv'
        s = 0
    }

    const master_data: any = []
    const full_dirty_data: any = []
    const readFile = (file: PathLike, data: any): Promise<void> => new Promise((resolve, reject) => {
        fs.createReadStream(file)
            .pipe(csv())
            .on('data', (d) => {
                // console.log(d)
                const row: any = {}
                for (const i in d) {
                    row[i.replace(/[^a-zA-Z ]/g, '')] = d[i]
                }
               data.push(row)
            })
            .on('end', () => {
                console.log('read csv at '.concat(file.toString()));
                resolve()
            });
    })

    await readFile(master_data_fp, master_data)
    await readFile(full_dirty_data_fp, full_dirty_data)

    /* const h_space: Hypothesis[] = scenarios[s].hypothesis_space as Hypothesis[]
    const target_fds: string[] = scenarios[s].cfds
    const fds: string[] = [] as string[]
    h_space.forEach((h) => {
        fds.push(h.cfd)
    })
    const fd_metadata: FD[] = [] as FD[]
    h_space.forEach((h) => {
        const p: number = calculateP(h.cfd, fds, master_data)
        const new_fd: FD = {
            fd: h.cfd,
            lhs: h.cfd.split(' => ')[0].replace('(', '').replace(')', '').split(', '),
            rhs: h.cfd.split(' => ')[1].split(', '),
            curr_p: target_fds.includes(h.cfd) ? 1/(target_fds.length) : 0,
            p_history: [],
            support: h.support,
            vios: h.vios,
        }
        fd_metadata.push(new_fd)
    })

    let curr_p_sum = 0
    fd_metadata.forEach((fd) => {
        curr_p_sum += fd.curr_p
    })
    fd_metadata.forEach((fd) => {
        fd.curr_p /= curr_p_sum
        console.log('p('.concat(fd.fd, '): ', fd.curr_p.toString()))
        fd.p_history.push(fd.curr_p)
    }) */

    console.log(s.toString())
    console.log(master_data_fp)

    let header: string[] = [] as string[]
    let project_id: string = ''
    try {
        const response = await axios.post('http://localhost:5000/duo/api/import', { scenario_id: s.toString() })
        const res = JSON.parse(response.data)
        header = res.header
        project_id = res.project_id
    } catch (err) {
        console.error(err)
    }
    console.log(project_id)

    let num_dirty_tuples: number = 0
    for (const i in master_data) {
        if (JSON.stringify(master_data[i]) !== JSON.stringify(full_dirty_data[i])) {
            num_dirty_tuples++
        }
    }

    console.log(num_dirty_tuples)

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

    console.log('got master data')
    let msg = '';

    console.log('initialized feedback object')

    let iter: number = 0
    while (msg !== '[DONE]') {
        iter++
        console.log('iter: '.concat(iter.toString()))
        const feedbackMap = buildFeedbackMap(data, feedback, header);

        /* Oracle behavior */
        for (const i in data) {
            const row = Object.keys(data[i]).reduce((filtered: any, key: string) => {
                if (key !== 'id') {
                    if (typeof (data[i][key]) === 'number') filtered[key] = data[i][key].toString();
                    else filtered[key] = data[i][key]
                }
                return filtered;
            }, {})
            if (JSON.stringify(row) !== JSON.stringify(master_data[data[i].id])) {
                for (const col in row) {
                    if (row[col] !== master_data[data[i].id][col]) {
                        feedbackMap[i][col] = true
                    }
                }
            }
        }

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
                        }
                        if (!Number.isNaN(row[j]) && Math.ceil(parseFloat(row[j])) - parseFloat(row[j]) === 0) {
                            row[j] = Math.ceil(row[j]).toString();
                        }
                    }
                }
            }
            else {
                console.log('Results:')
                /* fd_metadata.forEach((fd) => {
                    console.log(fd.fd + ': ' + fd.p_history.join(', '))
                }) */
            }
        } catch (err) {
            console.error(err);
            msg = '[DONE]';
        }
    }
}

const s: number = parseInt(process.argv[2])
run(s)
