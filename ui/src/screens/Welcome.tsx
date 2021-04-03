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
    Segment
} from 'semantic-ui-react'
import server from '../utils/server'

interface WelcomeProps {}

export const Welcome: FC<WelcomeProps> = () => {

    const [scenarios, setScenarios] = useState<string[] | null>(null)
    const [processing, setProcessing] = useState<boolean>(false)
    const [email, setEmail] = useState<string>('')

    const history = useHistory()

    const handleGetStarted = async () => {
        setProcessing(true)
        const response: AxiosResponse = await server.post(
            '/start',
            { email }
        )
        const s = response.data.scenarios as string[]
        setScenarios(s)
    }

    useEffect(() => {
        if (scenarios && scenarios.length < 4) {
            history.push('/interact', {
                email,
                scenarios
            })
        } else {
            handleGoToIntake()
        }
    }, [scenarios])

    const handleGoToIntake = () => {
        history.push('/start', { email, scenarios })
    }

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Grid.Row className='content-centered'>
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Duo</span>
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