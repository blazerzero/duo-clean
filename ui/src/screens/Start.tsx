import { AxiosResponse } from 'axios'
import React, { FC, useState, useEffect } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
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

interface StartProps {}

export const Start: FC<StartProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { email, scenarios } = location.state as any

    const [processing, setProcessing] = useState<boolean>(false)

    useEffect(() => {
        history.push('/interact', { email, scenarios })
    }, [])

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>

            </Grid>
            <Dimmer active={processing}>
                <Loader active={processing} size='big'>
                    Loading
                </Loader>
            </Dimmer>
        </Dimmer.Dimmable>
    )
}