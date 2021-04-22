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
    Divider,
    Header,
    Input,
    Radio,
    Checkbox,
    Dropdown
} from 'semantic-ui-react'
import { HiMenu, HiSortAscending, HiSortDescending } from 'react-icons/hi'
import server from '../utils/server'
import logo from '../images/OSU_horizontal_2C_O_over_B.png'

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
    const [fd, setFD] = useState<{[key: string]: string}>({})
    const [lhs, setLHS] = useState<string[]>([])
    const [rhs, setRHS] = useState<string[]>([])
    const [fdComment, setFDComment] = useState<string>('')
    const [doesntKnowFD, setDoesntKnowFD] = useState<boolean>(false)
    const [done, setDone] = useState<boolean>(false)
    
    useEffect(() => {
        const init_fd: {[key: string]: string} = {}
        header.forEach((h: string) => init_fd[h] = 'N/A')
        setFD(init_fd)
    }, [header])

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

    const handleDone = async () => {
        setProcessing(true)
        // const answers = { fd, durationNeeded }
        let header: string[]
        const response: AxiosResponse = await server.post('/post-interaction', {
            next_scenario_id: scenarios.length > 0 ? scenarios[0].toString() : '0',
            prev_scenario_id: scenario_id.toString(),
            email,
        })
        header = response.data.header

        
        // if (response.status === 201) {
        //     setHeader(response.data.header)
        //     setQuizDone(true)
        // } else {
        //     console.error(response.status)
        //     console.error(response.data.msg)
        // }
        const idx: number = scenarios.findIndex((s: number) => s === parseInt(scenario_id))
        setProcessing(false)
        if (idx === -1) {
            history.push('/post-interaction', {
                email,
                scenarios,
                scenario_id,
                header,
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

    const handleSubmit = async (isDone: boolean) => {
        if (isDone) {
            handleDone()
            return
        }

        setProcessing(true)
        // handle submit
        const fdbck: any = {}
        for (let i = 0; i < data.length; i++) {
            fdbck[data[i]['id']] = feedbackMap[i]
        }
        const lhs: string[] = Object.keys(fd).filter((k: string) => fd[k] === 'LHS')
        lhs.sort()
        const rhs: string[] = Object.keys(fd).filter((k: string) => fd[k] === 'RHS')
        rhs.sort()
        const current_user_h: string = `(${lhs.join(', ')}) => ${rhs.join(', ')}`
        console.log(current_user_h)
        const response: AxiosResponse = await server.post(
            '/feedback',
            {
                feedback: fdbck,
                project_id,
                current_user_h: doesntKnowFD ? 'Not Sure' : current_user_h,
                user_h_comment: fdComment,
            }
        )
        const { msg } = response.data
        if (msg === '[DONE]') {
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
            const re_init_fd: {[key: string]: string} = {}
            header.forEach((h: string) => re_init_fd[h] = 'N/A')
            setFDComment('')
            setIterCount(iter)
            setFeedback(new_fdbck)
            setFeedbackMap(feedback_map)
            setSortMethod(sorting)
            setProcessing(false)
            setData(prepped_data)
            setFD(re_init_fd)
            setDoesntKnowFD(false)
            setLHS([])
            setRHS([])
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

    const isValidFD = () => {
        return Object.keys(fd).filter((k: string) => fd[k] === 'LHS').length !== 0
        && Object.keys(fd).filter((k: string) => fd[k] === 'RHS').length !== 0
    }

    const buildFD = (attrs: any, side: 'LHS' | 'RHS') => {
        if (attrs) {
            console.log(attrs)
            const fresh_fd: {[key: string]: string} = {}
            header.forEach((h: string) => {
                fresh_fd[h] = fd[h]
            })
            attrs.forEach((attr: string) => {
                fresh_fd[attr] = side
            })
            header.forEach((h: string) => {
                if (!attrs.includes(h) && fresh_fd[h] === side) fresh_fd[h] = 'N/A'
            })
            console.log(fresh_fd)
            if (side === 'LHS') setLHS(attrs)
            else setRHS(attrs)
            setFD(fresh_fd)
        }
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page'>
                <Grid.Column>
                    <Grid.Row className='content-centered'>
                        <Container className='section' style={{ backgroundColor: 'white', position: 'absolute', top: 0, right: 0, width: '10vw', maxWidth: '500px', height: '8vh', borderBottomLeftRadius: 20 }} >
                            <img src={logo} style={{ padding: 10, position: 'absolute', top: 0, right: 0, width: '100%', height: 'auto' }} alt='OSU logo' />
                        </Container>
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Discovering Patterns in Data</span>
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
                            <p>Yellow cells indicate cells you marked as part of an exception to an FD.</p>
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
                                                    header.map((j: string) => {
                                                        // if (j === 'id') return
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
                        <Message>
                            <Message.Header>
                                <h3>
                                    Given all the data you've seen up until this point, what rule are you most confident holds over the data?
                                </h3>
                                <p>Indicate your answer using the dropdowns below. Pick one or more attributes for each side of the FD.</p>
                            </Message.Header>
                            <div style={{ flexDirection: 'row' }}>
                                <Dropdown
                                    placeholder='Select an attribute(s)...'
                                    multiple
                                    selection
                                    options={header.filter((h: string) => fd[h] !== 'RHS').map((h: string) => ({ key: h, text: h, value: h }))}
                                    onChange={(_e, props) => buildFD(props.value, 'LHS')}
                                    value={lhs}
                                />
                                <span style={{ paddingLeft: 10, paddingRight: 10, fontSize: 20 }}><strong>{'=>'}</strong></span>
                                <Dropdown
                                    placeholder='Select an attribute(s)...'
                                    multiple
                                    selection
                                    options={header.filter((h: string) => fd[h] !== 'LHS').map((h: string) => ({ key: h, text: h, value: h }))}
                                    onChange={(_e, props) => buildFD(props.value, 'RHS')}
                                    value={rhs}
                                />
                            </div>
                            {
                                !isValidFD() && !doesntKnowFD && (
                                    <Message error>
                                        You must either select at least one attribute for the LHS and one for the RHS, or check "I Don't Know."
                                    </Message>
                                )
                            }
                            <h3 style={{ paddingTop: 10, paddingBottom: 10 }}>OR</h3>
                            <Checkbox
                                label={`I Don't Know`}
                                name='idk_checkbox'
                                value='IDK'
                                checked={doesntKnowFD}
                                onChange={() => setDoesntKnowFD(!doesntKnowFD)}
                                style={{ paddingBottom: 10 }}
                            />
                            <Divider />
                            <Input
                                fluid
                                style={{ paddingTop: 10 }}
                                type='text'
                                size='large'
                                placeholder='Add any comments supporting your thinking here...'
                                onChange={(_e, props) => setFDComment(props.value)}
                                value={fdComment}
                            />
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row>
                        <Grid.Column className='content-centered'>
                            <Grid.Row>
                                <Button positive size='big' onClick={() => handleSubmit(false)} disabled={!isValidFD() && !doesntKnowFD}>Next</Button>
                                <Button
                                    color='grey'
                                    size='big'
                                    onClick={() => handleSubmit(true)}
                                    disabled={iterCount <= 8 || (!doesntKnowFD && !isValidFD())}>
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