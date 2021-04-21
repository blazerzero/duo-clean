import { AxiosResponse } from 'axios'
import { url } from 'node:inspector'
import React, { FC, useEffect, useRef, useState } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import {
    Button,
    Image,
    Loader,
    Container,
    Grid,
    Dimmer,
    Segment,
    Message,
    Divider,
    List,
    Table,
    Tab,
    Form,
    Radio,
    Input,
    Checkbox,
    Dropdown
} from 'semantic-ui-react'
import server from '../utils/server'
import logo from '../images/OSU_horizontal_2C_O_over_B.png'

interface PostInteractionProps {}

export const PostInteraction: FC<PostInteractionProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { header, email, scenarios, scenario_id } = location.state as any
    // console.log(scenarios)

    const [processing, setProcessing] = useState<boolean>(false)
    const [fd, setFD] = useState<{[key: string]: string}>({})
    const [doesntKnowFD, setDoesntKnowFD] = useState<boolean>(false)
    const [fdComment, setFDComment] = useState<string>('')
    const [dataOverviewRead, setDataOverviewRead] = useState<boolean>(false)
    const [done, setDone] = useState<boolean>(false)
    const [comments, setComments] = useState<string>('')

    useEffect(() => {
        const init_fd: {[key: string]: string} = {}
        header.forEach((h: string) => init_fd[h] = 'N/A')
        setFD(init_fd)
    }, [header])

    const scenarioDetails: {[key: number]: {[key: string]: string | null }} = {
        15: {
            domain: 'Movie',
            info: `
            This dataset describes information about various English-language movies and TV shows,
            such as the title of the movie or TV show, the type of program it is (e.g. movie or TV episode), and
            its MPAA or FCC rating (e.g. PG-13, R, TV-14).
            `,
            note: null
        },
        8: {
            domain: 'Airport',
            info: `
            This dataset describes information about various airports and airfields, including the name of
            the airfield, the type of airfield it is (airport, heliport, or seaplane base), and the person,
            group, or entity managing the airfield.
            `,
            note: 'Some airfields have no manager, and these are listed with a manager value of "NO MANAGER."'
        },
        14: {
            domain: 'Movie',
            info: `
            This dataset describes information about various English-language movies and TV shows,
            including the title of the movie of TV show, the genre of the program, the type of program
            it is (e.g. movie or TV episode), and what year the program was released in.
            `,
            note: null
        },
        11: {
            domain: 'Airport',
            info: `
            This dataset describes information about various airports and airfields, including the name of
            the airfield, the person, group, or entity that owns the airfield, and the person, group, or
            entity that owns the airfield.
            `,
            note: 'Some airfields have no manager, and these are listed with a manager value of "NO MANAGER."'
        },
        13: {
            domain: 'Airport',
            info: `
            This dataset describes information about various airports and airfields, including the name of
            the airfield, the person, group, or entity that owns the airfield, and the person, group, or
            entity that owns the airfield.
            `,
            note: 'Some airfields have no manager, and these are listed with a manager value of "NO MANAGER."'
        }
    }

    // const handleQuizDone = async () => {
    //     const answers = { fd, durationNeeded }
    //     const response: AxiosResponse = await server.post('/post-interaction', {
    //         email,
    //         scenario_id,
    //         next_scenario_id: scenarios[0].toString(),
    //         answers
    //     })
    //     if (response.status === 201) {
    //         setHeader(response.data.header)
    //         setQuizDone(true)
    //     } else {
    //         console.error(response.status)
    //         console.error(response.data.msg)
    //     }
    // }

    const handleReady = async () => {
        setProcessing(true)
        const next_scenario: number = scenarios.splice(0, 1) as number
        const lhs: string[] = Object.keys(fd).filter((k: string) => fd[k] === 'LHS')
        lhs.sort()
        const rhs: string[] = Object.keys(fd).filter((k: string) => fd[k] === 'RHS')
        rhs.sort()
        const initial_fd: string = `(${lhs.join(', ')}) => ${rhs.join(', ')}`
        console.log(initial_fd)
        const response: AxiosResponse = await server.post('/import', {
            email,
            scenario_id: next_scenario.toString(),
            initial_fd: doesntKnowFD ? 'Not Sure' : initial_fd,
            fd_comment: fdComment,
        })
        const { project_id, description } = response.data
        console.log(header)
        history.push('/interact', {
            email,
            scenarios,
            scenario_id: next_scenario.toString(),
            header,
            project_id,
            description
        })
    }

    const handleDoneComments = async (mode: 'skip' | 'submit') => {
        setProcessing(true)
        const response: AxiosResponse = await server.post('/done', {
            email,
            comments: mode === 'submit' ? comments : '',
        })
        if (response.status === 201) {
            setProcessing(false)
            setDone(true)
        }
    }

    const isValidFD = () => {
        return Object.keys(fd).filter((k: string) => fd[k] === 'LHS').length !== 0
        && Object.keys(fd).filter((k: string) => fd[k] === 'RHS').length !== 0
    }

    const buildFD = (attrs: any, side: 'LHS' | 'RHS') => {
        if (attrs) {
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
            setFD(fresh_fd)
        }
        isValidFD()
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Grid.Row>
                        <Container className='section' style={{ backgroundColor: 'white', position: 'absolute', top: 0, right: 0, width: '10vw', maxWidth: '500px', height: '8vh', borderBottomLeftRadius: 20 }} >
                            <img src={logo} style={{ padding: 10, position: 'absolute', top: 0, right: 0, width: '100%', height: 'auto' }} alt='OSU logo' />
                        </Container>
                        <Container className='content-centered home-header box-blur'>
                            <span className='home-title'>Discovering Patterns in Data</span>
                        </Container>
                        <Message success>
                            <Message.Header>
                                <h1>Scenario Complete</h1>
                            </Message.Header>
                            <p>
                                {
                                    scenarios.length > 0
                                    ? `You completed a scenario! Let's take a look at your next dataset now.`
                                    : `You completed your last scenario!`
                                }
                            </p>
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row>
                    {
                        scenarios.length > 0 ? (
                            <Message>
                                <Message.Header>
                                    {/* {
                                        scenarios.length > 1 ? 'Your Next Dataset' : 'Your Last Dataset'
                                    } */}
                                    <h2>Your Next Dataset</h2>
                                </Message.Header>
                                <Divider />
                                <h3>{`${scenarioDetails[scenarios[0]].domain} Data`}</h3>
                                <p>
                                    {scenarioDetails[scenarios[0]].info}
                                </p>
                                {
                                    scenarioDetails[scenarios[0]].note && (
                                        <p>
                                            <strong>NOTE: </strong>{scenarioDetails[scenarios[0]].note}
                                        </p>
                                    )
                                }
                                <Divider />
                                <Message>
                                    <Message.Header>
                                        <h3>
                                            This dataset has the following attributes: [{header.join(', ')}]. What FD do you think holds with the fewest exceptions?
                                        </h3>
                                    </Message.Header>
                                    <p>E.g. {'(facilityname) => type, owner'}; {'(title, year) => director'}</p>
                                    <h4>Answer by indicating, for each attribute below, whether the attribute is part of the LHS, RHS, or not part of the rule.</h4>
                                    <p><strong>NOTE: </strong>If you're not sure yet, you can check "I Don't Know" instead.</p>
                                    <Divider />
                                    <div style={{ flexDirection: 'row' }}>
                                    <Dropdown
                                        placeholder='Select an attribute(s)...'
                                        multiple
                                        selection
                                        options={header.filter((h: string) => fd[h] !== 'RHS').map((h: string) => ({ key: h, text: h, value: h }))}
                                        onChange={(_e, props) => buildFD(props.value, 'LHS')}
                                    />
                                    <span style={{ paddingLeft: 10, paddingRight: 10, fontSize: 20 }}><strong>{'=>'}</strong></span>
                                    <Dropdown
                                        placeholder='Select an attribute(s)...'
                                        multiple
                                        selection
                                        options={header.filter((h: string) => fd[h] !== 'LHS').map((h: string) => ({ key: h, text: h, value: h }))}
                                        onChange={(_e, props) => buildFD(props.value, 'RHS')}
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
                                    />
                                    <Divider style={{ paddingBottom: 10, paddingTop: 10 }} />
                                    <Input
                                        type='text'
                                        size='large'
                                        placeholder='Add any comments supporting your thinking here...'
                                        onChange={(_e, props) => setFDComment(props.value)}
                                    />
                                </Message>
                                {
                                    dataOverviewRead ? (
                                        <Message color='green'><p>Scroll Down</p></Message>
                                    ) : (
                                        <Button positive size='big' onClick={() => setDataOverviewRead(true)} disabled={!doesntKnowFD && !isValidFD()}>Continue</Button>
                                    )
                                }
                                {
                                    dataOverviewRead && (
                                        <>
                                            <Divider />
                                            <Message info>
                                                <Message.Header>
                                                    When you're ready to begin interacting with your next dataset, click "Go to the Data" below.
                                                </Message.Header>
                                            </Message>
                                            <Button positive size='big' onClick={handleReady}>Go to the Data</Button>
                                        </>
                                    )
                                }
                            </Message>
                        ) : (
                            <Message success>
                                {
                                    done ? (
                                        <>
                                            <Message.Header>
                                                Thanks for participating in our study!
                                            </Message.Header>
                                        </>
                                    ) : (
                                        <>
                                            <Message.Header>
                                                You're all done! How did everything go? Leave any comments or feedback you have about your study experience below!
                                            </Message.Header>
                                            <Input
                                                fluid
                                                type='text'
                                                size='large'
                                                placeholder='Add any comments or feedback here...'
                                                onChange={(_e, props) => setComments(props.value)}
                                                style={{ paddingTop: 20, paddingBottom: 20}}
                                            />
                                            <div style={{ flexDirection: 'row' }}>
                                                <Button color='grey' size='big' onClick={() => handleDoneComments('skip')} style={{ marginRight: 10 }}>Skip</Button>
                                                <Button positive size='big' onClick={() => handleDoneComments('submit')}>Submit</Button>
                                            </div>
                                        </>
                                    )
                                }
                            </Message>
                        )
                    }
                    </Grid.Row>
                    <Grid.Row>
                        
                    </Grid.Row>
                            {/* </>
                        )
                    } */}
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