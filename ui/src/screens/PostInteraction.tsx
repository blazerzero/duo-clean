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
    Input
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
    const [fd, setFD] = useState<string>('')
    const [nextFD, setNextFD] = useState<string>('')
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
        const response: AxiosResponse = await server.post('/import', {
            email,
            scenario_id: next_scenario.toString(),
            initial_fd: nextFD,
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

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Grid.Row>
                        <Container className='section' style={{ backgroundColor: 'white', position: 'absolute', top: 0, right: 0, width: '10vw', maxWidth: '500px', height: '8vh', borderBottomLeftRadius: 20 }} >
                            <img src={logo} style={{ padding: 10, position: 'absolute', top: 0, right: 0, width: '100%', height: 'auto' }} alt='OSU logo' />
                        </Container>
                        <Container className='content-centered home-header box-blur'>
                            <span className='home-title'>Discovering Functional Dependencies</span>
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
                                <p>
                                    You'll have up to 15 rounds to give feedback before moving on to the next dataset.
                                </p>
                                <p>
                                    One round is defined as giving feedback by marking any cells you believe are part
                                    of violations, clicking "Next," and letting us know what you think the dominant
                                    FD is over the data given everything you've seen so far.
                                </p>
                                <p>
                                    <strong>NOTE: </strong>
                                    You do not need to worry about knowing or finding the right value for a cell! This is
                                    not an error detection problem. Your goal is just to find violations of FDs.
                                </p>
                                <Message>
                                    <Message.Header>
                                        <h3>
                                            This dataset has the following attributes: [{header.join(', ')}]. Given this
                                            schema, what do you think should be the primary FD(s) that holds over this dataset?
                                        </h3>
                                    </Message.Header>
                                    <p>E.g. facilityname determines type and owner; title and year determine director</p>
                                    <p><strong>NOTE: </strong>If you're not sure yet, you can leave this empty.</p>
                                    <Input
                                        size='large'
                                        placeholder='Enter the FD(s) here'
                                        onChange={(_e, props) => setNextFD(props.value)}
                                        className='input'
                                    />
                                </Message>
                                {
                                    dataOverviewRead ? (
                                        <Message color='green'><p>Scroll Down</p></Message>
                                    ) : (
                                        <Button positive size='big' onClick={() => setDataOverviewRead(true)} disabled={nextFD.length === 0}>Continue</Button>
                                    )
                                }
                                {
                                    dataOverviewRead && (
                                        <>
                                            <Divider />
                                            <Message info>
                                                <Message.Header>
                                                    When you're ready to begin working on your next dataset, click "Let's Go" below.
                                                </Message.Header>
                                            </Message>
                                            <Button positive size='big' onClick={handleReady}>Let's Go!</Button>
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