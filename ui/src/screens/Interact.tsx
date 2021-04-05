import { AxiosError, AxiosResponse } from 'axios'
import React, { FC, useState, useEffect } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import {
    Button,
    Form,
    Modal,
    Loader,
    Container,
    Grid,
    Dimmer,
    Segment,
    Table,
    Message,
    Divider
} from 'semantic-ui-react'
import { HiMenu, HiSortAscending, HiSortDescending } from 'react-icons/hi'
import server from '../utils/server'

interface InteractProps {}

export const Interact: FC<InteractProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { email, scenario_id, project_id, description, header, scenarios } = location.state as any

    const [data, setData] = useState<{[key: string]: string}[]>([])
    const [feedback, setFeedback] = useState<any[]>([])
    const [feedbackMap, setFeedbackMap] = useState<{[key: string]: {[key: string]: boolean}}>({})
    const [processing, setProcessing] = useState<boolean>(false)
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
                const fdbck = JSON.parse(response.data.feedback)

                const sample_object = JSON.parse(sample)

                const prepped_data = prepareSample(sample_object)
                const feedback_map = buildFeedbackMap(prepped_data, fdbck)
                const iter = iterCount + 1
                const sorting: {[key: string]: string} = {}
                header.forEach((h: string) => {
                    sorting[h] = 'NONE'
                })
                setSortMethod(sorting)
                setIterCount(iter)
                setFeedback(fdbck)
                setFeedbackMap(feedback_map)
                setProcessing(false)
                setData(prepped_data)
            })
            .catch((error: AxiosError) => console.error(error))
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const handleDone = () => {
        const idx: number = scenarios.findIndex((s: number) => s === parseInt(scenario_id))
        
        if (idx === -1) {
            history.push('/post-interaction', {
                email,
                scenarios,
                scenario_id,
            })
        }
    }

    const prepareSample = (sample: any) => {
        const rows: any[] = Object.values(sample)
        for (let i = 0; i < rows.length; i++) {
            for (let j in rows[i]) {
                if (j === 'id') continue
                if (rows[i][j] === null) rows[i][j] = ''
                else if (typeof rows[i][j] != 'string') rows[i][j] = rows[i][j].toString()
                if (!isNaN(parseInt(rows[i][j])) && Math.ceil(parseFloat(rows[i][j])) - parseFloat(rows[i][j]) === 0) {
                    rows[i][j] = Math.ceil(parseInt(rows[i][j])).toString();
                }
            }
        }
        return rows
    }

    const buildFeedbackMap = (sample: any, fdbck: any) => {
        const feedback_map: any = {}
        const rows = Object.keys(sample)
        const cols = ['id', ...header]
        for (let i = 0; i < rows.length; i++) {
            var tup: any = {}
            for (let j = 0; j < cols.length; j++) {
                var cell = fdbck.find((e: any) => {
                    var trimmedCol = cols[j].replace(/[\n\r]+/g, '')
                    return e.row === parseInt(sample[rows[i]]['id']) && e.col === trimmedCol
                })
                tup[cols[j]] = cell.marked
            }
            feedback_map[rows[i]] = tup
        }
        return feedback_map
    }

    const handleCellClick = async (key: string) => {
        // handle cell click
        const pieces: string[] = key.split('_')

        const idx: number = parseInt(pieces.shift() || '-1')
        if (idx === -1) return
        const id: number = parseInt(data[idx]['id'])
        const attr: string = pieces.join('_')
        const fdbck: any = [...feedback]
        const cell = fdbck.findIndex((e: any) => {
            const trimmedCol: string = attr.replace(/[\n\r]+/g, '')
            return e.row === id && e.col === trimmedCol
        })
        fdbck[cell].marked = !fdbck[cell].marked
        const feedback_map = {...feedbackMap}
        feedback_map[idx][attr] = !feedback_map[idx][attr]
        setFeedbackMap(feedback_map)
        setFeedback(fdbck)
    }

    const handleSubmit = async () => {
        setProcessing(true)
        // handle submit
        const fdbck: any = {}
        for (let i = 0; i < data.length; i++) {
            fdbck[data[i]['id']] = feedbackMap[i]
        }
        const response: AxiosResponse = await server.post(
            '/feedback',
            {
                feedback: fdbck,
                project_id
            }
        )
        const { msg } = response.data
        if (msg === '[DONE]') {
            alert('')
            handleDone()
        } else {
            const { sample } = response.data
            const new_fdbck = JSON.parse(response.data.feedback)
            const sample_object = JSON.parse(sample)
            const prepped_data = prepareSample(sample_object)
            const feedback_map = buildFeedbackMap(prepped_data, new_fdbck)
            const sorting: {[key: string]: string} = {}
            header.forEach((h: string) => {
                sorting[h] = 'NONE'
            })
            const iter = iterCount + 1
            setIterCount(iter)
            setFeedback(new_fdbck)
            setFeedbackMap(feedback_map)
            setSortMethod(sorting)
            setProcessing(false)
            setData(prepped_data)
        }
    }

    const handleSort = async (attr: string) => {
        const method = {...sortMethod}
        let feedback_map: {[key: string]: {[key: string]: boolean}} = {}
        const sample: {[key: string]: string}[] = data
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
        setFeedbackMap(feedback_map)
        setData(sample)
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page'>
                <Grid.Column>
                    <Grid.Row className='content-centered'>
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Duo</span>
                        </Container>
                    </Grid.Row>
                    <Grid.Row className='content-centered' style={{ paddingBottom: 10 }}>
                        <Message info>
                            <Message.Header>
                                <h4>Need help using the interface or a refresher on the data you're working with?</h4>
                            </Message.Header>
                            <p><a style={{ color: 'blue' }} href="https://github.com/blazerzero/duo-help/blob/master/README.md" target='_blank' rel='noopener noreferrer'>Click here!</a></p>
                        </Message>
                    </Grid.Row>
                    <Grid.Row className='content-centered'>
                        <Message color='yellow'>
                            <Message.Header><h3>Remember!</h3></Message.Header>
                            <p>Yellow cells indicate cells you marked as violations of a key or FD.</p>
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row className='content-centered'>
                        {
                            JSON.stringify(Object.keys(data)) === JSON.stringify(Object.keys(feedbackMap)) && (
                                <Container className='content-centered'>
                                    <Table celled size='large'>
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
                                            Object.entries(data).map(([_, row], i) => (
                                                <Table.Row key={row.id}>
                                                {
                                                    Object.keys(row).map((j) => {
                                                        if (j === 'id') return
                                                        var key = `${i}_${j}`
                                                        return feedbackMap[i][j] ? (
                                                            <Table.Cell
                                                                key={key}
                                                                style={{ backgroundColor: '#FFF3CD'}}
                                                                onClick={() => handleCellClick(key)}>
                                                                {row[j]}
                                                            </Table.Cell>
                                                        ) : (
                                                            <Table.Cell
                                                                key={key}
                                                                onClick={() => handleCellClick(key)}>
                                                                {row[j]}
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
                    <Divider />
                    <Grid.Row>
                        <Grid.Column className='content-centered'>
                            <Grid.Row>
                                <Button positive size='big' onClick={handleSubmit}>Next</Button>
                                <Button
                                    color='grey'
                                    size='big'
                                    onClick={handleDone}
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