import { AxiosError, AxiosResponse } from 'axios'
import React, { FC, useState, useEffect } from 'react'
import { useHistory, useLocation, useParams } from 'react-router-dom'
import {
    Button,
    Form,
    Modal,
    Input,
    Loader,
    Container,
    Grid,
    Dimmer,
    Segment,
    Table,
    Message
} from 'semantic-ui-react'
import { HiMenu, HiSortAscending, HiSortDescending } from 'react-icons/hi'
import server from '../utils/server'

interface InteractProps {}

export const Interact: FC<InteractProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { email, scenario_id, project_id, description, header, scenarios } = location.state as any

    const [data, setData] = useState<any>([])
    const [feedback, setFeedback] = useState<{[key: string]: {[key: string]: any}}>({})
    const [feedbackMap, setFeedbackMap] = useState<{[key: string]: {[key: string]: boolean}}>({})
    const [processing, setProcessing] = useState<boolean>(false)
    const [done, setDone] = useState<boolean>(false)
    const [sortMethod, setSortMethod] = useState<{[key: string]: string}>({})
    const [iterCount, setIterCount] = useState<number>(0)

    useEffect(() => {
        setProcessing(true)
        // set sorting
        const sorting: {[key: string]: string} = {}
        header.forEach((attr: string) => {
            sorting[attr] = 'NONE'
        })

        // get sample
        server.post('/sample', { project_id })
            .then((response: AxiosResponse) => {
                const { sample, msg } = response.data
                const fdbck = response.data.feedback
                console.log(msg)

                const prepped_data = prepareSample(sample)
                const feedback_map = buildFeedbackMap(prepped_data, fdbck)
                const iter = iterCount + 1
                setIterCount(iter)
                setData(prepped_data)
                setFeedback(fdbck)
                setFeedbackMap(feedback_map)
                setProcessing(false)
            })
            .catch((error: AxiosError) => console.log(error))
    }, [])

    useEffect(() => {
        // handle done
        const idx: number = scenarios.findIndex((s: number) => s === scenario_id)
        if (idx !== -1) {
            scenarios.splice(idx, 1)
            history.push('/post-interaction', {
                email,
                scenarios,
            })
        }
    }, [done])

    const prepareSample = (sample: any) => {
        for (let i in sample) {
            for (let j in sample) {
                if (j === 'id') break

                if (sample[i][j] === null) sample[i][j] = ''
                else if (typeof data[i][j] != 'string') sample[i][j] = sample[i][j].toString()
                if (!isNaN(parseInt(sample[i][j])) && Math.ceil(parseFloat(sample[i][j])) - parseFloat(sample[i][j]) === 0) {
                    sample[i][j] = Math.ceil(parseInt(sample[i][j])).toString();
                }
            }
        }
        return sample
    }

    const buildFeedbackMap = (sample: any, feedback: any) => {
        const fMap = {}
        const rows = Object.keys(sample)
        const cols = header
        for (let i = 0; i < rows.length; i++) {
            var tup: any = {}
            for (let j = 0; j < cols.length; j++) {
                var cell = feedback.find((e: any) => {
                    var trimmedCol = cols[j].replace(/[\n\r]+/g, '')
                    return e.row === parseInt(data[rows[i]]['id']) && e.col === trimmedCol
                });
                tup[cols[j]] = cell.marked
            }
            feedbackMap[rows[i]] = tup
          }
        console.log(feedbackMap)
        return feedbackMap
    }

    const handleCellClick = async (key: string) => {
        // handle cell click
        const pieces: string[] = key.split('_')
        const idx: number = parseInt(pieces.shift() || '-1')
        if (idx !== -1) return
        const id: number = parseInt(data[idx]['id'])
        const attr: string = pieces.join('_')
        const fdbck: any = feedback
        const cell = fdbck.findIndex((e: any) => {
            const trimmedCol: string = attr.replace(/[\n\r]+/g, '')
            return e.row === parseInt(data[idx]['id']) && e.col === trimmedCol
        })
        fdbck[cell].marked = !fdbck[cell].marked
        const feedback_map = feedbackMap
        feedback_map[idx][attr] = !feedback_map[idx][attr]
        setFeedback(fdbck)
        setFeedbackMap(feedback_map)
    }

    const handleSubmit = async () => {
        setProcessing(true)
        // handle submit
        const fdbck: any = {}
        for (const f in feedbackMap) {
            fdbck[data[f]['id']] = feedbackMap[f]
        }
        const response: AxiosResponse = await server.post(
            '/feedback',
            {
                feedback: fdbck,
                projectID: project_id
            }
        )
        const res = JSON.parse(response.data)
        const { msg } = res
        if (msg === '[DONE]') {
            alert('')
            setDone(true)
        } else {
            const { sample } = res
            const fdbck = res.feedback
            const prepped_data = prepareSample(sample)
            const feedback_map = buildFeedbackMap(sample, fdbck)
            const sorting: {[key: string]: string} = {}
            header.forEach((h: string) => {
                sorting[h] = 'NONE'
            })
            const iter = iterCount + 1
            setIterCount(iter)
            setData(prepped_data)
            setFeedback(fdbck)
            setFeedbackMap(feedbackMap)
            setSortMethod(sorting)
            setProcessing(false)
        }
    }

    const handleSort = async (attr: string) => {
        const method = sortMethod
        let feedback_map: {[key: string]: {[key: string]: boolean}} = {}
        const sample = data
        // handle sort change for attr
        switch (method[attr]) {
            case 'NONE':
                header.forEach((h: string) => {
                    if (h === attr) {
                        method[h] = 'ASC'
                    } else method[h] = 'NONE'
                })
                // ascending sort
                sample.sort((a: any, b: any) => {
                    return a[attr] > b[attr] ? 1 : -1
                })
                break
            case 'DESC':
                header.forEach((h: string) => {
                    if (h === attr) {
                        method[h] = 'ASC'
                    } else method[h] = 'NONE'
                })
                // ascending sort
                sample.sort((a: any, b: any) => {
                    return a[attr] > b[attr] ? 1 : -1
                })
                break
            case 'ASC':
                header.forEach((h: string) => {
                    if (h === attr) {
                        method[h] = 'DESC'
                    } else method[h] = 'NONE'
                })
                // ascending sort
                sample.sort((a: any, b: any) => {
                    return a[attr] < b[attr] ? 1 : -1
                })
                break
            default:
                break
        }
        feedback_map = buildFeedbackMap(sample, feedback)
        setSortMethod(method)
        setData(sample)
        setFeedbackMap(feedbackMap)
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page'>
                <Grid.Column>
                    <Grid.Row className='content-centered'>
                        <Container className='results-header box-blur'>
                            <span className='results-title'>Duo</span>
                            <p><strong>Scenario Description: </strong>{description}</p>
                        </Container>
                    </Grid.Row>
                    <Grid.Row className='content-centered'>
                        <Grid.Column width={7}>
                            <Message color='yellow'>
                                <Message.Header>Remember!</Message.Header>
                                <p>Yellow cells indicate cells you marked as violations of a key or FD.</p>
                            </Message>
                        </Grid.Column>
                        {
                            Object.keys(data).length > 0 && (
                                <Container className='content-centered'>
                                    <Table celled>
                                        <Table.Header>
                                            <Table.Row>
                                            {
                                                header.map((item: string) => (
                                                    <Table.HeaderCell key={`header_${item}`}>
                                                        {item}
                                                        {
                                                            sortMethod[item] === 'ASC'
                                                            ? <HiSortDescending onClick={() => handleSort(item)} cursor='pointer' />
                                                            : (
                                                                sortMethod[item] === 'DESC'
                                                                ? <HiSortAscending onClick={() => handleSort(item)} cursor='pointer' />
                                                                : <HiMenu onClick={() => handleSort(item)} cursor='pointer' />
                                                            )
                                                        }
                                                    </Table.HeaderCell>
                                                ))
                                            }
                                            </Table.Row>
                                        </Table.Header>

                                        <Table.Body>
                                        {
                                            Object.keys(data).map((i) => (
                                                <Table.Row key={i}>
                                                {
                                                    Object.keys(data[i]).map((j) => {
                                                        if (j === 'id') return;
                                                        var key = `${i}_${j}`
                                                        return (
                                                            <Table.Cell
                                                                key={key}
                                                                style={{ cursor: 'pointer', backgroundColor: (!!feedbackMap[i][j] ? '#FFF3CD' : 'white')}}
                                                                onClick={() => handleCellClick(key)}>
                                                                {data[i][j]}
                                                            </Table.Cell>
                                                        )
                                                    })
                                                }
                                                </Table.Row>
                                            ))
                                        }
                                        </Table.Body>
                                    </Table>
                                </Container>
                            )
                        }
                    </Grid.Row>
                    <Grid.Row>
                        <Grid.Column width={8}></Grid.Column>
                        <Grid.Column width={4}>
                            <Grid.Row>
                                <Button positive size='big' onClick={handleSubmit}>Next</Button>
                                <Button
                                    color='grey'
                                    size='big'
                                    onClick={() => setDone(true)}
                                    disabled={iterCount <= 5}>
                                    I'm All Done
                                </Button>
                            </Grid.Row>
                        </Grid.Column>
                    </Grid.Row>
                </Grid.Column>
            </Grid>
            <Dimmer active={processing}>
                <Loader active={processing} size='big'>
                    Loading
                </Loader>
            </Dimmer>
        </Dimmer.Dimmable>
    )
}