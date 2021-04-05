import { AxiosResponse } from 'axios'
import { url } from 'node:inspector'
import React, { FC, useRef, useState } from 'react'
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

interface PostInteractionProps {}

export const PostInteraction: FC<PostInteractionProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { email, scenarios, scenario_id } = location.state as any

    const [processing, setProcessing] = useState<boolean>(false)
    const [fd, setFD] = useState<string>('')
    const [durationNeeded, setDurationNeeded] = useState<string>('')
    const [quizDone, setQuizDone] = useState<boolean>(false)

    const handleReady = async () => {
        setProcessing(true)
        const answers = { fd, durationNeeded }
        const response: AxiosResponse = await server.post('/post-interaction', {
            email,
            scenario_id,
            answers
        })
        if (response.status === 201) {
            const next_scenario: number = scenarios.splice(0, 1) as number
            const response2: AxiosResponse = await server.post('/import', {
                email,
                scenario_id: next_scenario.toString(),
            })
            const { header, project_id, description } = response2.data
            console.log(header)
            history.push('/interact', {
                email,
                scenarios,
                scenario_id: next_scenario.toString(),
                header,
                project_id,
                description
            })
        } else {
            console.error(response.status)
            console.error(response.data.msg)
        }
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Grid.Row className='content-centered'>
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Duo</span>
                        </Container>
                        <Message success className='content-centered'>
                            <Message.Header>
                                <h1>Scenario Complete</h1>
                            </Message.Header>
                            <p>
                                You completed a scenario! We just have a couple of questions
                                about your thinking process throughout your interaction with the dataset.
                            </p>
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row className='content-centered'>
                        <Message className='content-centered'>
                            <Message.Header>
                                <h3>
                                    At the end of your interaction with the data, what did you
                                    think was the key in the dataset, or the functional dependency
                                    (FD) that the errors in the dataset were based on?
                                </h3>
                            </Message.Header>
                            <p>E.g. facilityname was the key; title and year determine director</p>
                            <Container style={{ padding: 20 }}>
                                <Input
                                    size='large'
                                    placeholder='Enter the FD or key here'
                                    onChange={(_e, props) => setFD(props.value)}
                                    className='input'
                                />
                            </Container>
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row className='content-centered'>
                        <Message className='content-centered'>
                            <Message.Header>
                                <h3>
                                    How long do you think it took you to reach this conclusion?
                                </h3>
                            </Message.Header>
                            <Container style={{ padding: 20 }}>
                                <Form>
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
                                            label='After a few rounds'
                                            name='radioGroup'
                                            value='after-a-few-rounds'
                                            checked={durationNeeded === 'after-a-few-rounds'}
                                            onChange={() => setDurationNeeded('after-a-few-rounds')}
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
                            </Container>
                            {
                                quizDone ? (
                                    <Message color='green'><p>Scroll Down</p></Message>
                                ) : (
                                    <Button positive size='big' disabled={fd === '' || durationNeeded === ''}onClick={() => setQuizDone(true)}>Submit</Button>
                                )
                            }
                            {
                                quizDone && (
                                    <>
                                        <Divider />
                                        {
                                            scenarios.length > 0 ? (
                                            <>
                                                <Message info>
                                                    <Message.Header>
                                                        When you're ready to move onto the next dataset, click "Continue" below.
                                                    </Message.Header>
                                                </Message>
                                                <Button positive size='big' onClick={handleReady}>Continue</Button>
                                            </>
                                            ) : (
                                                <Message success>
                                                    <Message.Header>
                                                        You're all done! Thanks for participating in our study!
                                                    </Message.Header>
                                                </Message>
                                            )
                                        }
                                    </>
                                )
                            }
                        </Message>
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