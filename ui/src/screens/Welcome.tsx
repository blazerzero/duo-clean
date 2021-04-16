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
    Image
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
                            <span className='home-title'>Discovering Functional Dependencies</span>
                        </Container>
                        <Form>
                            <Form.Field>
                                <Container className='section'>
                                    <Input
                                        type='email'
                                        size='large'
                                        label='Email Address: '
                                        placeholder='Enter your email address'
                                        onChange={(_e, props) => setEmail(props.value)}
                                        className='input'
                                    />
                                </Container>
                            </Form.Field>
                            <Container className='section'>
                                <Button
                                    positive
                                    size='big'
                                    type='submit'
                                    disabled={email === '' || !email.includes('@')}
                                    onClick={handleGetStarted}
                                >
                                    Get Started
                                </Button>
                            </Container>
                        </Form>
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