import { AxiosResponse } from 'axios'
import React, { FC, useState, useEffect } from 'react'
import { useHistory } from 'react-router-dom'
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
    Image,
    Message,
    Divider
} from 'semantic-ui-react'
import server from '../utils/server'
import logo from '../images/OSU_horizontal_2C_O_over_B.png'

interface WelcomeProps {}

export const Welcome: FC<WelcomeProps> = () => {

    const [processing, setProcessing] = useState<boolean>(false)
    const [email, setEmail] = useState<string>('')

    const history = useHistory()

    const handleGetStarted = async () => {
        setProcessing(true)
        const response: AxiosResponse = await server.post(
            '/start',
            { email }
        )
        const scenarios = response.data.scenarios
        if (response.status === 201 || scenarios.length === 4) {
            history.push('/start', { email, scenarios })
        } else if (response.status === 200) {
            alert(`Welcome back! You have ${scenarios.length} datasets left to go.`)
            const next_scenario: number = scenarios.splice(0, 1) as number
            const response2: AxiosResponse = await server.post('/import', {
                email,
                scenario_id: next_scenario.toString(),
            })
            const { header, project_id, description } = response2.data
            history.push('/interact', {
                email,
                scenarios,
                scenario_id: next_scenario.toString(),
                header,
                project_id,
                description
            })
        }
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Grid.Row className='content-centered'>
                        <Container className='section' style={{ backgroundColor: 'white', position: 'absolute', top: 0, right: 0, width: '10vw', maxWidth: '500px', height: '8vh', borderBottomLeftRadius: 20 }} >
                            <img src={logo} style={{ padding: 10, position: 'absolute', top: 0, right: 0, width: '100%', height: 'auto' }} alt='OSU logo' />
                        </Container> 
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Discovering Patterns in Data</span>
                        </Container>
                    </Grid.Row>
                    <Grid.Row>
                        <Message>
                            <Message.Header>
                                <h1>Hello!</h1>
                                <Divider />
                                <p><strong>Thank you so much for agreeing to participate in our study!</strong></p>
                            </Message.Header>
                            <p>
                                Our goal is to understand how humans discover patterns in data.
                            </p>
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row>
                        <Message>
                            <Message.Header>
                                <h2>Your Role</h2>
                            </Message.Header>
                            <Divider />
                            <p>
                                You will analyze five different datasets interactively. You will see only a small sample of
                                each dataset. Your job will be to predict the <strong>pattern</strong> that most
                                reasonably holds over the entire dataset.
                            </p>                     
                        </Message>
                    </Grid.Row>
                    <Divider />
                    <Grid.Row>
                        <Message>
                            <Message.Header>
                                <h3>Enter your email address to get started!</h3>
                            </Message.Header>
                            <Divider />
                            <Form>
                                <Form.Field>
                                    <Input
                                        type='email'
                                        size='large'
                                        label='Email Address: '
                                        placeholder='Enter your email address'
                                        onChange={(_e, props) => setEmail(props.value)}
                                    />
                                </Form.Field>
                                <Button
                                    positive
                                    size='big'
                                    type='submit'
                                    disabled={email === '' || !email.includes('@')}
                                    onClick={handleGetStarted}
                                >
                                    Get Started
                                </Button>
                            </Form>
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