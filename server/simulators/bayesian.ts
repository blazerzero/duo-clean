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
import Chance from 'chance'
import { factorial } from 'mathjs'
import * as scenarios from './scenarios.json'

interface Hypothesis {
    cfd: string,
    score: number,
    conf: number,
    support: number[],
    vios: number[],
    vio_pairs: number[][]
}

interface FD {
    fd: string,
    lhs: string[],
    rhs: string[],
    curr_p: number
    p_history: number[],
    support: number[],
    vios: number[],
    vio_pairs: number[][]
}

interface AttrP {
    attr: string,
    p: number
}

function buildFeedbackMap(data: any, feedback: any, header: any): any {
    const feedbackMap: any = {};
    const rows = Object.keys(data);
    // console.log(data)
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

function calculateP(fd: string, all_fds: string[], data: any): number {
    const lhs: string[] = fd.split(' => ')[0].replace('(', '').replace(')', '').split(', ')
    const wUV: AttrP[] = [] as AttrP[]
    const wAC: AttrP[] = [] as AttrP[]

    const wAC_def: AttrP[] = [
        { attr: 'type', p: 0.4 },
        { attr: 'region', p: 0.6 },
        { attr: 'facilityname', p: 0.9 },
        { attr: 'owner', p: 0.9 },
        { attr: 'ownertype', p: 0.5 },
        { attr: 'manager', p: 0.75 },
        { attr: 'listingnumber', p: 0.9 },
        { attr: 'title', p: 0.8 },
        { attr: 'year', p: 0.3 },
        { attr: 'rating', p: 0.75 },
        { attr: 'director', p: 0.6 },
        { attr: 'userrating', p: 0.1 },
        { attr: 'name', p: 0.8 },
        { attr: 'areacode', p: 0.7 },
        { attr: 'phone', p: 0.5 },
        { attr: 'state', p: 0.4 },
        { attr: 'zip', p: 0.3 },
    ]
    let wUV_sum: number = 0
    let wAC_sum: number = 0
    lhs.forEach((lh) => {
        // UV
        // console.log(lh)
        const uv: Set<string> = new Set<string>()
        for (const row of data) {
            uv.add(row[lh].toString())
        }
        wUV.push({
            attr: lh,
            p: uv.size / data.length,
        })

        wUV_sum += (uv.size / data.length)

        // AC
        let idx: AttrP | undefined = wAC_def.find((a) => a.attr === lh)
        if (idx === undefined) {
            idx = {
                attr: lh,
                p: 0,
            }
        }
        wAC.push({
            attr: lh,
            p: idx.p,
        })

        wAC_sum += idx.p
    })

    const wUV_avg: number = wUV_sum / wUV.length
    const wAC_avg: number = wAC_sum / wAC.length

    // SetRelation
    const subset_cfds: string[] = [] as string[]
    const superset_cfds: string[] = [] as string[]

    all_fds.forEach((f) => {
        const f_lhs: string[] = f.split(' => ')[0].replace('(', '').replace(')', '').split(', ')
        if (f_lhs.every((v) => lhs.includes(v) === true)) {
            subset_cfds.push(f.split(' => ')[0].replace('(', '').replace(')', ''))
        }
        if (lhs.every((v) => f_lhs.includes(v) === true)) {
            superset_cfds.push(f.split(' => ')[0].replace('(', '').replace(')', ''))
        }
    })

    const similar_cfd_set: Set<string> = new Set<string>()
    similar_cfd_set.add(fd.split(' => ')[0].replace('(', '').replace(')', ''))
    subset_cfds.forEach((sc) => {
        similar_cfd_set.add(sc)
    })
    superset_cfds.forEach((sc) => {
        similar_cfd_set.add(sc)
    })
    const similar_cfds: string[][] = [] as string[][]
    similar_cfd_set.forEach((scs) => {
        similar_cfds.push(scs.split(', '))
    })
    similar_cfds.sort((a, b) => a.length - b.length)

    const lhs_idx: number = similar_cfds.findIndex((l) => l === lhs)
    const wSR: number = (similar_cfds.length - lhs_idx) / similar_cfds.length

    const weight: number = harmonic([wUV_avg, wAC_avg, wSR])
    return weight
}

function shuffleFDs(fds: FD[]) {
    for (let i = fds.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [fds[i], fds[j]] = [fds[j], fds[i]];
    }
    return fds
}

function pickFD(fds: FD[], p_max: number): FD | null {
    let cumul = 0
    const shuffled_fds: FD[] = shuffleFDs(fds)
    for (let i = 0; i < fds.length; i++) {
        // console.log(fd.curr_p)
        cumul += fds[i].curr_p
        // console.log(random)
        // console.log(cumul)
        if (cumul >= p_max) {
            // console.log('done!')
            return fds[i]
        }
    }
    return null
}

async function run(s: number, type: string) {
    const chance: Chance.Chance = new Chance()
    const p_max: number = type === 'informed' ? 0.9 : 0.5

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

    const h_space: Hypothesis[] = scenarios[s].hypothesis_space as Hypothesis[]
    const target_fds: string[] = scenarios[s].cfds
    const fds: string[] = [] as string[]
    h_space.forEach((h: Hypothesis) => {
        fds.push(h.cfd)
    })
    const fd_metadata: FD[] = [] as FD[]
    const X: number[][] = [] as number[][]
    h_space.forEach((h: Hypothesis) => {
        // const p: number = calculateP(h.cfd, fds, master_data)
        const new_fd: FD = {
            fd: h.cfd,
            lhs: h.cfd.split(' => ')[0].replace('(', '').replace(')', '').split(', '),
            rhs: h.cfd.split(' => ')[1].split(', '),
            curr_p: type === 'informed' ? ((h.support.length - h.vios.length) / h.support.length) : 0.5,
            p_history: [],
            support: h.support,
            vios: h.vios,
            vio_pairs: h.vio_pairs
        }
        fd_metadata.push(new_fd)
        for (const vp of h.vio_pairs) {
            if (!X.includes(vp)) {
                X.push(vp)
            }
        }
    })

    /* let curr_p_sum = 0
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

    let data: any
    let feedback: any
    let vios: number[][]
    const p_X: number[] = [] as number[]
    try {
        console.log('before sample')
        const response = await axios.post('http://localhost:5000/duo/api/sample', { project_id })
        console.log('after sample')
        const res = JSON.parse(response.data)
        const { sample, sample_vios } = pick(res, ['sample', 'sample_vios'])
        // console.log(sample_vios)
        vios = sample_vios
        console.log(vios)
        //feedback = JSON.parse(res.feedback)
        data = Object.values(JSON.parse(sample))
        console.log('parsed data')
        for (const i in data) {
            const row: any = data[i]
            for (const j in row) {
                if (j === 'id') break;

                if (row[j] == null) row[j] = '';
                else if (typeof row[j] !== 'string') row[j] = row[j].toString()
                if (!Number.isNaN(row[j]) && Math.ceil(parseFloat(row[j])) - parseFloat(row[j]) === 0) {
                    row[j] = Math.ceil(row[j]).toString()
                }
            }
        }
        const curr_p_X: number = (factorial(vios.length) * factorial(X.length - vios.length)) / factorial(X.length)
        p_X.push(curr_p_X)
        console.log('prepped data')
    } catch (err) {
        console.error(err);
    }

    console.log('got master data')
    let msg = '';

    console.log('initialized feedback object')

    const dirty_tuples: number[] = [] as number[]
    for (const i in data) {
        const row = Object.keys(data[i]).reduce((filtered: any, key: string) => {
            if (key !== 'id') {
                if (typeof (data[i][key]) === 'number') filtered[key] = data[i][key].toString();
                else filtered[key] = data[i][key]
            }
            return filtered;
        }, {})
        if (JSON.stringify(row) !== JSON.stringify(master_data[data[i].id])) {
            dirty_tuples.push(data[i].id)
        }
    }

    /* Reinforce FDs */
    fd_metadata.forEach((fd) => {
        let p_X_given_h: number = 1
        /* for (const i in data) {
            const sample_row = Object.keys(data[i]).reduce((filtered: any, key: string) => {
                if (key !== 'id') {
                    if (typeof (data[i][key]) === 'number') filtered[key] = data[i][key].toString();
                    else filtered[key] = data[i][key]
                }
                return filtered;
            }, {})
            if (JSON.stringify(sample_row) !== JSON.stringify(master_data[data[i].id])) {

                counter++
                if (fd.vios.includes(data[i].id)) {
                    p_X_given_h *= (1/fd.vios.length)
                } else {
                    p_X_given_h = 0
                    break
                }
            }
        } */
        // console.log(vios)
        /* for (const vio of vios) {
            p_X_given_h *= (all_vios.includes(vio) ? (1-fd.curr_p) : fd.curr_p)
        }
        let p_X: number = 1
        for (let i = 0; i < vios.length; i++) {
            p_X *= 1/(all_vios.length - i)
        }
        const new_p: number = p_X_given_h === 0 ? 0 : (fd.curr_p * p_X_given_h) / p_X
        fd.curr_p = new_p */
    })

    let iter: number = 0
    while (msg !== '[DONE]') {
        iter++
        console.log('iter: '.concat(iter.toString()))
        const feedbackMap = buildFeedbackMap(data, feedback, header);

        let numMarkedTuples: number = 0;
        let numMarkedCells: number = 0;

        /* Bayesian behavior */
        /* const strong_fds: FD[] = [] as FD[]
        const strong_fd_ps: number[] = [] as number[]
        fd_metadata.forEach((fd) => {
            if (fd.curr_p >= p_max) {
                strong_fds.push(fd)
                strong_fd_ps.push(fd.curr_p)
            }
        })
        if (strong_fds.length > 0) {
            for (const i in data) {
                const chosen_fd: FD = chance.weighted(strong_fds, strong_fd_ps)
                if (chosen_fd.vios.includes(data[i].id)) {
                    header.forEach((col) => {
                        if (chosen_fd.rhs.includes(col)) {
                            feedbackMap[i][col] = true
                        }
                        else {
                            feedbackMap[i][col] = false
                        }
                    })
                }
                else {
                    header.forEach((col) => {
                        feedbackMap[i][col] = false
                    })
                }
            }
        } */

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
                const { sample, sample_vios } = pick(res, ['sample', 'sample_vios']);
                feedback = JSON.parse(res.feedback);
                data = Object.values(JSON.parse(sample));
                vios = sample_vios

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

                /* Reinforce FDs */
                fd_metadata.forEach((fd) => {
                    let p_X_given_h: number = 1
                    /* for (const i in data) {
                        const sample_row = Object.keys(data[i]).reduce((filtered: any, key: string) => {
                            if (key !== 'id') {
                                if (typeof (data[i][key]) === 'number') filtered[key] = data[i][key].toString();
                                else filtered[key] = data[i][key]
                            }
                            return filtered;
                        }, {})
                        if (JSON.stringify(sample_row) !== JSON.stringify(master_data[data[i].id])) {

                            counter++
                            if (fd.vios.includes(data[i].id)) {
                                // p_X_given_h *= (1/fd.vios.length)
                                p_X_given_h *= (1 - fd.curr_p)
                            } else {
                                // p_X_given_h = 0
                                p_X_given_h *= fd.curr_p
                                break
                            }
                        }
                    } */
                    /* for (const vio of vios) {
                        if (vio.length === 3) {
                            p_X_given_h *= (fd.vio_trios.includes(vio) ? (1-fd.curr_p) : fd.curr_p)
                        } else if (vio.length === 2) {
                            p_X_given_h *= (fd.vio_pairs.includes(vio) ? (1-fd.curr_p) : fd.curr_p)
                        } else {
                            p_X_given_h *= (fd.vios.includes(vio[0]) ? (1-fd.curr_p) : fd.curr_p)
                        }
                    }
                    let p_X: number = 1
                    for (let i = 0; i < vios.length; i++) {
                        p_X *= 1/(all_vios.length - i)
                    } */
                    /* for (let i = 0; i < counter; i++) {
                        p_X *= 1/(num_dirty_tuples - i)
                    } */
                    // const new_p: number = p_X_given_h === 0 ? 0 : (fd.curr_p * p_X_given_h) / p_X
                    // fd.curr_p = new_p
                })

                // NORMALIZE WEIGHTS
                /* curr_p_sum = 0
                fd_metadata.forEach((fd) => {
                    curr_p_sum += fd.curr_p
                }) */
                fd_metadata.forEach((fd) => {
                    // fd.curr_p /= curr_p_sum
                    console.log('p('.concat(fd.fd, '): ', fd.curr_p.toString()))
                    fd.p_history.push(fd.curr_p)
                })
            }
            else {
                console.log('Results:')
                fd_metadata.forEach((fd) => {
                    console.log(fd.fd + ': ' + fd.p_history.join(', '))
                })
            }
        } catch (err) {
            console.error(err);
            msg = '[DONE]';
        }
    }
}

const s: number = parseInt(process.argv[2])
const type: string = process.argv[3]
run(s, type)
