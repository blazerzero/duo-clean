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
import logo from '../images/OSU_horizontal_2C_O_over_B.png'

interface StartProps {}

export const Start: FC<StartProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { email, scenarios } = location.state as any

    const [processing, setProcessing] = useState<boolean>(false)
    const [yourRoleRead, setYourRoleRead] = useState<boolean>(false)
    const [interfaceGuideRead, setInterfaceGuideRead] = useState<boolean>(false)
    const [dataOverviewRead, setDataOverviewRead] = useState<boolean>(false)
    const [fdReviewRead, setFDReviewRead] = useState<boolean>(false)
    const [quizDone, setQuizDone] = useState<boolean>(false)
    const [quizAnswersReviewed, setQuizAnswersReviewed] = useState<boolean>(false)
    const [header, setHeader] = useState<string[]>([])
    const [fd, setFD] = useState<string>('')

    const [q1Response, setQ1Response] = useState<string>('')
    const q1CorrectAnswer = 'name'
    const [q2Response, setQ2Response] = useState<string>('')
    const q2CorrectAnswers = ['5_305', '7_305', '5_FL', '7_CA']
    const scenarioDetails: {[key: number]: {[key: string]: string | null }} = {
        6: {
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
        10: {
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
        }
    }

    const handleQuizDone = async () => {
        setProcessing(true)
        const answers = [
            {
                answer: q1Response,
                correctAnswer: q1CorrectAnswer,
                correct: q1Response === q1CorrectAnswer
            },
            {
                answer: q2Response,
                correctAnswer: q2CorrectAnswers,
                correct: q2CorrectAnswers.includes(q2Response)
            }
        ]
        const first_scenario: number = scenarios[0] as number
        const response: AxiosResponse = await server.post('/pre-survey', {
            email,
            scenario_id: first_scenario.toString(),
            answers
        })
        setQuizDone(true)
        setHeader(response.data.header)
        setProcessing(false)
    }

    const handleReady = async () => {
        setProcessing(true)
        const first_scenario: number = scenarios.splice(0, 1) as number
        const response: AxiosResponse = await server.post('/import', {
            email,
            scenario_id: first_scenario.toString(),
            initial_fd: fd,
        })
        const { project_id, description } = response.data
        history.push('/interact', {
            email,
            scenarios,
            scenario_id: first_scenario.toString(),
            header,
            project_id,
            description
        })
        setProcessing(false)
    }

    const fdExampleData = [
        {
            id: 1,
            address: '123 Elm St',
            city: 'Portland',
            state: 'OR',
            zip: 97123,
        },
        {
            id: 2,
            address: '777 Broadway',
            city: 'Seattle',
            state: 'WA',
            zip: 98108,
        },
        {
            id: 3,
            address: '800 6th Ave',
            city: 'Portland',
            state: 'OR',
            zip: 97209,
        },
        {
            id: 4,
            address: '250 Irving St',
            city: 'Los Angeles',
            state: 'CA',
            zip: 90254,
        },
        {
            id: 5,
            address: '515 Marshall St',
            city: 'Portland',
            state: 'OR',
            zip: 97123,
        },
        {
            id: 6,
            address: '800 6th Ave',
            city: 'Portland',
            state: 'ME',
            zip: 97209,
        }
    ]

    const q1Data = [
        {
            name: 'Michael',
            areacode: 503,
            phone: 1111111,
            state: 'OR',
            zip: 97007
        },
        {
            name: 'Nate',
            areacode: 206,
            phone: 3333333,
            state: 'WA',
            zip: 98802
        },
        {
            name: 'Leilani',
            areacode: 808,
            phone: 4444444,
            state: 'HI',
            zip: 96850
        },
        {
            name: 'Mitchell',
            areacode: 541,
            phone: 1234567,
            state: 'OR',
            zip: 97401
        },
        {
            name: 'Samantha',
            areacode: 206,
            phone: 4353245,
            state: 'WA',
            zip: 43153
        },
        {
            name: 'Mitchell',
            areacode: 541,
            phone: 1234567,
            state: 'OR',
            zip: 97401
        },
    ]

    const q2Data = [
        {
            id: 2,
            name: 'Darrell',
            areacode: 775,
            phone: 1354785,
            state: 'NV',
            zip: 89501
        },
        {
            id: 3,
            name: 'Henry',
            areacode: 404,
            phone: 8546984,
            state: 'GA',
            zip: 30334
        },
        {
            id: 4,
            name: 'Blake',
            areacode: 775,
            phone: 8415641,
            state: 'NV',
            zip: 89501
        },
        {
            id: 5,
            name: 'Jusuf',
            areacode: 305,
            phone: 2547889,
            state: 'FL',
            zip: 33130
        },
        {
            id: 6,
            name: 'Shania',
            areacode: 775,
            phone: 5598465,
            state: 'NV',
            zip: 89501
        },
        {
            id: 7,
            name: 'Ellen',
            areacode: 305,
            phone: 9874587,
            state: 'CA',
            zip: 33128
        },
    ]

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Grid.Row>
                        <Container className='section' style={{ backgroundColor: 'white', position: 'absolute', top: 0, right: 0, width: '10vw', maxWidth: '500px', height: '8vh', borderBottomLeftRadius: 20 }} >
                            <img src={logo} style={{ padding: 10, position: 'absolute', top: 0, right: 0, width: '100%', height: 'auto' }} alt='OSU logo' />
                        </Container>
                        <Container className='content-centered home-header box-blur'>
                            <span className='home-title'>Discovering Keys and Functional Dependencies</span>
                        </Container>
                        <Message>
                            <Message.Header>
                                <h1>Hello!</h1>
                                <Divider />
                                <p><strong>Thank you so much for agreeing to participate in our study!</strong></p>
                            </Message.Header>
                            <p>
                                We are analyzing and aim to model how users learn data quality rules and patterns
                                (i.e. keys and functional dependencies) that apply over datasets.
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
                                You will be tasked with detecting and marking violations of keys or 
                                functional dependencies (FDs) in some datasets.
                            </p>
                            <p>
                                You will be interacting with four different datasets that may contain
                                violations of one or more keys or FDs. Your job will be to think about
                                the key(s) or FD(s) that exist in the dataset and find exceptions to
                                those rules.
                            </p>
                            {
                                yourRoleRead ? (
                                    <Message color='green'><p>Scroll Down</p></Message>
                                ) : (
                                    <Button
                                        positive 
                                        size='big' 
                                        onClick={() => {
                                            setYourRoleRead(true)
                                        }}
                                    >
                                        Continue
                                    </Button>
                                )
                            }                            
                        </Message>
                    </Grid.Row>
                    {
                        yourRoleRead && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message>
                                        <Message.Header>
                                            <h2>Let's Review FDs and Keys</h2>
                                        </Message.Header>
                                        <Divider />
                                        <Message info>
                                            <Message.Header>
                                                <h3>What is an FD?</h3>
                                            </Message.Header>
                                            <p>
                                                A <strong>functional dependency</strong>, or <strong>FD</strong>, is an expression 
                                                that explains how attributes in a dataset are dependent on each other.
                                            </p>
                                            <p>
                                                A <strong>key</strong> is a special type of FD in which an attribute or set of attributes functionally determines
                                                every other attribute in the dataset.
                                            </p>
                                        </Message>
                                        <p>
                                            For example, in the dataset below, a building's street address (e.g. 123 Elm St) functionally determines
                                            the building's city, state, and ZIP code, as these three values are dependent on the address. This FD is also
                                            a key, since address determines every other attribute in the tuple.
                                        </p>
                                        <Table>
                                            <Table.Header>
                                                <Table.Row>
                                                {
                                                    Object.keys(fdExampleData[0]).map((h: string) => h !== 'id' && (
                                                        <Table.HeaderCell key={h}>{h}</Table.HeaderCell>
                                                    ))
                                                }
                                                </Table.Row>
                                            </Table.Header>
                                            <Table.Body>
                                                {
                                                    fdExampleData.map((e) => e.id !== 6 && (
                                                        <Table.Row>
                                                            {
                                                                Object.entries(e).map(([k, v], _i) => k !== 'id' && (
                                                                    <Table.Cell>{v}</Table.Cell>
                                                                ))
                                                            }
                                                        </Table.Row>
                                                    ))
                                                }
                                            </Table.Body>
                                        </Table>
                                        <p>
                                            Another FD in this dataset is <strong>{'(city, zip) => state'}</strong>, which states that the city
                                            and ZIP code together uniquely identify the state.
                                        </p>
                                        <Message warning>
                                            <Message.Header>
                                                <h4>Some FDs functionally determine only attribute, while others determine many attributes.</h4>
                                            </Message.Header>
                                            <p>
                                                E.g. area code only determines state, but address determines city, state, and zip code.
                                            </p>
                                        </Message>
                                        <p>
                                            For more information on FDs and to see more examples, you can go <a href='https://en.wikipedia.org/wiki/Functional_dependency#Examples' target='_blank' rel='noopener noreferrer'>here</a>.
                                        </p>
                                        <Divider />
                                        <Message info>
                                            <Message.Header>
                                                <h3>What is a violation?</h3>
                                            </Message.Header>
                                            <p>
                                                If a tuple contains values that do not align with the rest of the dataset with
                                                respect to an FD or key (e.g. a tuple has a different value for "state" than any
                                                other tuples with same area code value), the tuple is said to <strong>violate</strong> the FD or key.
                                            </p>
                                        </Message>
                                        <p>
                                            Let's see the same dataset again. Here, the two tuples with the address "800 6th Ave" (highlighted below)
                                            form a violation of the FD <strong>{'(address) => city, state, zip'}</strong>, as two addresses with the
                                            same city and ZIP code have different states listed.
                                        </p>
                                        <Table>
                                            <Table.Header>
                                                <Table.Row>
                                                {
                                                    Object.keys(fdExampleData[0]).map((h: string) => h !== 'id' && (
                                                        <Table.HeaderCell key={h}>{h}</Table.HeaderCell>
                                                    ))
                                                }
                                                </Table.Row>
                                            </Table.Header>
                                            <Table.Body>
                                                {
                                                    fdExampleData.map((e) => e.id !== 1 && (
                                                        <Table.Row>
                                                            {
                                                                Object.entries(e).map(([k, v], _i) => k !== 'id' && (
                                                                    e.id === 3 || e.id === 6 ? (
                                                                        <Table.Cell style={{ backgroundColor: '#FFF3CD' }}>
                                                                            {v}
                                                                        </Table.Cell>
                                                                    ) : (
                                                                        <Table.Cell>{v}</Table.Cell>
                                                                    )
                                                                ))
                                                            }
                                                        </Table.Row>
                                                    ))
                                                }
                                            </Table.Body>
                                        </Table>
                                        {
                                            fdReviewRead ? (
                                                <Message color='green'><p>Scroll Down</p></Message>
                                            ) : (
                                                <Button positive size='big' onClick={() => setFDReviewRead(true)}>Continue</Button>
                                            )
                                        }
                                    </Message>
                                </Grid.Row>
                            </>
                        )
                    }
                    {
                        fdReviewRead && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message>
                                        <Message.Header>
                                            <h2>Knowledge Check</h2>
                                        </Message.Header>
                                        <Divider />
                                        <p>In the following table, which attribute is the key?</p>
                                        {
                                            quizDone && (
                                                <Message positive={q1Response === q1CorrectAnswer} negative={q1Response !== q1CorrectAnswer}>
                                                    <Message.Header>
                                                        {
                                                            q1Response === q1CorrectAnswer
                                                            ? 'Correct!'
                                                            : 'Incorrect'
                                                        }
                                                    </Message.Header>
                                                    {
                                                        q1Response !== q1CorrectAnswer && (
                                                            'The correct answer has been highlighted with a green box.'
                                                        )
                                                    }
                                                </Message>
                                            )
                                        }
                                        <Table>
                                            <Table.Header>
                                                <Table.Row>
                                                {
                                                    Object.keys(q1Data[0]).map((h: string) => (
                                                        <Table.HeaderCell key={h}>{h}</Table.HeaderCell>
                                                    ))
                                                }
                                                </Table.Row>
                                            </Table.Header>
                                            <Table.Body>
                                                {
                                                    q1Data.map((e) => {
                                                        return (
                                                            <Table.Row>
                                                                {
                                                                    Object.values(e).map((v) => (
                                                                        <Table.Cell>{v}</Table.Cell>
                                                                    ))
                                                                }
                                                            </Table.Row>
                                                        )
                                                    })
                                                }
                                            </Table.Body>
                                        </Table>
                                        <Form>
                                            <Form.Field>
                                                <Radio
                                                    label='areacode'
                                                    name='q1RadioGroup'
                                                    value='areacode'
                                                    checked={q1Response === 'areacode'}
                                                    onChange={() => !quizDone && setQ1Response('areacode')}
                                                />
                                            </Form.Field>
                                            <Form.Field>
                                                {
                                                    quizDone ? (
                                                        <Radio
                                                            style={{ border: '2px solid green', padding: 10 }}
                                                            label='name'
                                                            name='q1RadioGroup'
                                                            value='name'
                                                            checked={q1Response === 'name'}
                                                            onChange={() => !quizDone && setQ1Response('name')}
                                                        />
                                                    ) : (
                                                        <Radio
                                                            label='name'
                                                            name='q1RadioGroup'
                                                            value='name'
                                                            checked={q1Response === 'name'}
                                                            onChange={() => !quizDone && setQ1Response('name')}
                                                        />
                                                    )
                                                }
                                            </Form.Field>
                                            <Form.Field>
                                                <Radio
                                                    label='The combination of areacode and state'
                                                    name='q1RadioGroup'
                                                    value='combo'
                                                    checked={q1Response === 'combo'}
                                                    onChange={() => !quizDone && setQ1Response('combo')}
                                                />
                                            </Form.Field>
                                            <Form.Field>
                                                <Radio
                                                    label='zip'
                                                    name='q1RadioGroup'
                                                    value='zip'
                                                    checked={q1Response === 'zip'}
                                                    onChange={() => setQ1Response('zip')}
                                                />
                                            </Form.Field>
                                        </Form>
                                        <Divider />
                                        <p>The table below contains a violation of the FD <strong>(areacode) {'=>'} state.</strong></p>
                                        <p>Find the violation and mark one of the cells whose value is causing the violation.</p>
                                        {
                                            quizDone && (
                                                <Message positive={q2CorrectAnswers.includes(q2Response)} negative={!q2CorrectAnswers.includes(q2Response)}>
                                                    <Message.Header>
                                                        {
                                                            q2CorrectAnswers.includes(q2Response)
                                                            ? 'Correct!'
                                                            : 'Incorrect'
                                                        }
                                                    </Message.Header>
                                                    All possible correct answers have been highlighted in green.
                                                </Message>
                                            )
                                        }
                                        <Table>
                                            <Table.Header>
                                                <Table.Row>
                                                {
                                                    Object.keys(q2Data[0]).map((h: string) => (
                                                        <Table.HeaderCell key={h}>{h}</Table.HeaderCell>
                                                    ))
                                                }
                                                </Table.Row>
                                            </Table.Header>
                                            <Table.Body>
                                                {
                                                    q2Data.map((e) => {
                                                        return (
                                                            <Table.Row>
                                                                {
                                                                    Object.entries(e).map(([k, v], i) => {
                                                                        if (quizDone && q2CorrectAnswers.includes(`${e.id}_${v}`)) {
                                                                            return (
                                                                                <Table.Cell
                                                                                    key={`${e.id}_${v}`}
                                                                                    style={{backgroundColor: '#E5F9E6' }}
                                                                                >
                                                                                {v}
                                                                                </Table.Cell>
                                                                            )
                                                                        } else {
                                                                            return q2Response === `${e.id}_${v}`
                                                                            ? (
                                                                                <Table.Cell
                                                                                    key={`${e.id}_${v}`}
                                                                                    style={{ cursor: 'pointer', backgroundColor: '#FFF3CD' }}
                                                                                    onClick={() => {
                                                                                        if (!quizDone) {
                                                                                            setQ2Response('')
                                                                                        }
                                                                                    }}
                                                                                >
                                                                                {v}
                                                                                </Table.Cell>
                                                                            ) : (
                                                                                <Table.Cell
                                                                                    key={`${e.id}_${v}`}
                                                                                    style={{ cursor: 'pointer' }}
                                                                                    onClick={() => {
                                                                                        if (!quizDone) {
                                                                                            setQ2Response(`${e.id}_${v}`)
                                                                                        }
                                                                                    }}
                                                                                >
                                                                                {v}
                                                                                </Table.Cell>
                                                                            )
                                                                        }
                                                                    })
                                                                }
                                                            </Table.Row>
                                                        )
                                                    })
                                                }
                                            </Table.Body>
                                        </Table>
                                        {
                                            quizDone ? (
                                                quizAnswersReviewed ? (
                                                    <Message color='green'><p>Scroll Down</p></Message>
                                                ) : (
                                                    <>
                                                        <Message warning><p>Review Your Answers</p></Message>
                                                        <Button positive size='big' onClick={() => setQuizAnswersReviewed(true)}>Continue</Button>
                                                    </>
                                                )
                                            ) : (
                                                <Button positive size='big' disabled={q1Response === '' || q2Response === ''} onClick={handleQuizDone}>Submit</Button>
                                            )
                                        }
                                        
                                    </Message>
                                </Grid.Row>
                            </>
                        )
                    }
                    {
                        quizDone && quizAnswersReviewed && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message>
                                        <Message.Header>
                                            <h2>How to Interact With the Datasets</h2>
                                        </Message.Header>
                                        <Divider />
                                        <p>
                                            To mark a cell as part of a violation, click on the cell. The cell will be
                                            highlighted yellow.
                                        </p>
                                        <p>
                                            If you decide at any point that this cell is not part of a violation and want
                                            to undo your feedback for that cell, you can simply click on the cell
                                            again to unhighlight and unmark it.
                                        </p>
                                        <p>
                                            To submit your marks for that round, click "Next," and you'll be presented with
                                            a new sample from the dataset. If you don't see anything that should be marked,
                                            you don't have to mark anything, and you can just click "Next" to get a fresh sample.
                                        </p>
                                        <p>
                                            Your feedback will be visible throughout the entire interaction, i.e. if you 
                                            previously marked a cell as part of a violation and that tuple reappears in a sample later
                                            on, the cell will still be highlighted so that you can review and change your
                                            previous feedback alongside new data.
                                        </p>
                                        <p>
                                            If you have no more feedback left to give for the dataset or are otherwise
                                            done giving feedback, click "Done" to finish working with the dataset.
                                        </p>
                                        {
                                            interfaceGuideRead ? (
                                                <Message color='green'><p>Scroll Down</p></Message>
                                            ) : (
                                                <Button positive size='big' onClick={() => setInterfaceGuideRead(true)}>Continue</Button>
                                            )
                                        }
                                    </Message>
                                </Grid.Row>
                            </>
                        )
                    }
                    {
                        interfaceGuideRead && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message>
                                        <Message.Header>
                                            <h2>Your First Dataset</h2>
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
                                            not an error detection problem. Your goal is just to find violations of FDs or keys.
                                        </p>
                                        <Message>
                                            <Message.Header>
                                                <h3>
                                                    This dataset has the following attributes: [{header.join(', ')}]. Given this
                                                    schema, what do you think should be the primary FD(s) that holds over this dataset?
                                                </h3>
                                            </Message.Header>
                                            <p>E.g. facilityname is the key; title and year determine director</p>
                                            <Input
                                                size='large'
                                                placeholder='Enter the FD(s) or key(s) here'
                                                onChange={(_e, props) => setFD(props.value)}
                                                className='input'
                                            />
                                        </Message>
                                        {
                                            dataOverviewRead ? (
                                                <Message color='green'><p>Scroll Down</p></Message>
                                            ) : (
                                                <Button positive size='big' onClick={() => setDataOverviewRead(true)}>Continue</Button>
                                            )
                                        }
                                        {
                                            dataOverviewRead && (
                                                <>
                                                    <Divider />
                                                    <Message info>
                                                        <Message.Header>
                                                            When you're ready to begin, click "Let's Go" below.
                                                        </Message.Header>
                                                    </Message>
                                                    <Button positive size='big' onClick={handleReady}>Let's Go!</Button>
                                                </>
                                            )
                                        }
                                    </Message>
                                </Grid.Row>
                            </>
                        )
                    }
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