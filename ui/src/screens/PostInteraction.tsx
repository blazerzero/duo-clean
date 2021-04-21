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
    Checkbox
} from 'semantic-ui-react'
import server from '../utils/server'
import logo from '../images/OSU_horizontal_2C_O_over_B.png'

interface PostInteractionProps {}

export const PostInteraction: FC<PostInteractionProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { header, email, scenarios, scenario_id } = location.state as any
    console.log(scenarios)

    const [processing, setProcessing] = useState<boolean>(false)
    const [fd, setFD] = useState<{[key: string]: string}>({})
    const [doesntKnowFD, setDoesntKnowFD] = useState<boolean>(false)
    const [durationNeeded, setDurationNeeded] = useState<string>('')
    const [quizDone, setQuizDone] = useState<boolean>(false)
    const [dataOverviewRead, setDataOverviewRead] = useState<boolean>(false)
    // const [header, setHeader] = useState<string[]>([])

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
            initial_fd,
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

    const isValidFD = () => {
        return Object.keys(fd).filter((k: string) => fd[k] === 'LHS').length !== 0
        && Object.keys(fd).filter((k: string) => fd[k] === 'RHS').length !== 0
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
                            <span className='home-title'>Discovering Rules and Patterns in Data</span>
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
                    {/* <Divider />
                    <Grid.Row>
                        <Message>
                            <Message.Header>
                                <h3>
                                    At the end of your interaction with the data, what did you
                                    think was the key in the dataset, or the functional dependency
                                    (FD) that the errors in the dataset were based on?
                                </h3>
                            </Message.Header>
                            <p>E.g. facilityname was the key; title and year determine director</p>
                            <Input
                                size='large'
                                placeholder='Enter the FD or key here'
                                onChange={(_e, props) => setFD(props.value)}
                                className='input'
                            />
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row>
                        <Message>
                            <Message.Header>
                                <h3>
                                    How long do you think it took you to reach this conclusion?
                                </h3>
                            </Message.Header>
                            <Form style={{ paddingTop: 20, paddingBottom: 20 }}>
                                <Form.Field>
                                    <Radio
                                        label='I figured it out right away'
                                        name='radioGroup'
                                        value='right-away'
                                        checked={durationNeeded === 'right-away'}
                                        onChange={() => setDurationNeeded('right-away')}
                                    />
                                </Form.Field>
                                <Form.Field>
                                    <Radio
                                        label='After a couple of rounds'
                                        name='radioGroup'
                                        value='after-a-couple-of-rounds'
                                        checked={durationNeeded === 'after-a-couple-of-rounds'}
                                        onChange={() => setDurationNeeded('after-a-couple-of-rounds')}
                                    />
                                </Form.Field>
                                <Form.Field>
                                    <Radio
                                        label='About halfway through'
                                        name='radioGroup'
                                        value='halfway'
                                        checked={durationNeeded === 'halfway'}
                                        onChange={() => setDurationNeeded('halfway')}
                                    />
                                </Form.Field>
                                <Form.Field>
                                    <Radio
                                        label='Towards the end of the interaction'
                                        name='radioGroup'
                                        value='towards-the-end'
                                        checked={durationNeeded === 'towards-the-end'}
                                        onChange={() => setDurationNeeded('towards-the-end')}
                                    />
                                </Form.Field>
                            </Form>
                            {
                                quizDone ? (
                                    <Message color='green'><p>Scroll Down</p></Message>
                                ) : (
                                    <Button positive size='big' disabled={fd === '' || durationNeeded === ''} onClick={handleQuizDone}>Submit</Button>
                                )
                            }
                        </Message>
                    </Grid.Row> */}
                    {/* {
                        quizDone && (
                            <> */}
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
                                            This dataset has the following attributes: [{header.join(', ')}]. Given this
                                            schema, what rule are you most confident holds over this dataset?
                                        </h3>
                                    </Message.Header>
                                    <p>E.g. {'(facilityname) => type, owner'}; {'(title, year) => director'}</p>
                                    <h4>Answer by indicating, for each attribute below, whether the attribute is part of the LHS, RHS, or not part of the rule.</h4>
                                    <p><strong>NOTE: </strong>If you're not sure yet, you can check "I Don't Know" instead.</p>
                                    <Divider />
                                    <Checkbox
                                        label={`I Don't Know`}
                                        name='idk_checkbox'
                                        value='IDK'
                                        checked={doesntKnowFD}
                                        onChange={() => setDoesntKnowFD(!doesntKnowFD)}
                                    />
                                    <h3 style={{ paddingTop: 10, paddingBottom: 10 }}>OR</h3>
                                    {
                                        header.map((h: string) => (
                                            <div style={{ flexDirection: 'row' }}>
                                                <h4>{h}</h4>
                                                <Radio
                                                    style={{ padding: 10 }}
                                                    label='Left-hand side'
                                                    name={`${h}_radioGroup`}
                                                    value='LHS'
                                                    checked={Object.keys(fd).includes(h) && fd[h] === 'LHS'}
                                                    onChange={() => {
                                                        const newFD: {[key: string]: string} = {}
                                                        Object.keys(fd).forEach((h: string) => newFD[h] = fd[h])
                                                        newFD[h] = 'LHS'
                                                        setFD(newFD)
                                                    }}
                                                />
                                                <Radio
                                                    style={{ padding: 10 }}
                                                    label='Right-hand side'
                                                    name={`${h}_radioGroup`}
                                                    value='RHS'
                                                    checked={Object.keys(fd).includes(h) && fd[h] === 'RHS'}
                                                    onChange={() => {
                                                        const newFD: {[key: string]: string} = {}
                                                        Object.keys(fd).forEach((h: string) => newFD[h] = fd[h])
                                                        newFD[h] = 'RHS'
                                                        setFD(newFD)
                                                    }}
                                                />
                                                <Radio
                                                    style={{ padding: 10 }}
                                                    label='Not part of the rule'
                                                    name={`${h}_radioGroup`}
                                                    value='N/A'
                                                    checked={Object.keys(fd).includes(h) && fd[h] === 'N/A'}
                                                    onChange={() => {
                                                        const newFD: {[key: string]: string} = {}
                                                        Object.keys(fd).forEach((h: string) => newFD[h] = fd[h])
                                                        newFD[h] = 'N/A'
                                                        setFD(newFD)
                                                    }}
                                                />
                                            </div>
                                        ))
                                    }
                                    {
                                        !isValidFD() && !doesntKnowFD && (
                                            <Message error>
                                                You must select at least one attribute for the LHS and one for the RHS.
                                            </Message>
                                        )
                                    }
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
                                <Message.Header>
                                    You're all done! Thanks for participating in our study!
                                </Message.Header>
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