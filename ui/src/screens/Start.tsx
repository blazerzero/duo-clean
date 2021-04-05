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
    Radio
} from 'semantic-ui-react'
import server from '../utils/server'

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

    const [q1Response, setQ1Response] = useState<string>('')
    const q1CorrectAnswer = 'name'
    const [q2Response, setQ2Response] = useState<string>('')
    const q2CorrectAnswer = '5_FL'

    const handleReady = async () => {
        setProcessing(true)
        const answers = [
            {
                answer: q1Response,
                correctAnswer: q1CorrectAnswer,
                correct: q1Response === q1CorrectAnswer
            },
            {
                answer: q2Response,
                correctAnswer: q2CorrectAnswer,
                correct: q2Response === q2CorrectAnswer
            }
        ]
        const first_scenario: number = scenarios.splice(0, 1) as number
        const response: AxiosResponse = await server.post('/pre-survey', {
            email,
            scenario_id: first_scenario.toString(),
            answers
        })
        if (response.status === 201) {
            const response2: AxiosResponse = await server.post('/import', {
                email,
                scenario_id: first_scenario.toString(),
            })
            const { header, project_id, description } = response2.data
            history.push('/interact', {
                email,
                scenarios,
                scenario_id: first_scenario.toString(),
                header,
                project_id,
                description
            })
        } else {
            console.error(response.status)
            console.error(response.data.msg)
        }
    }

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
                    <Grid.Row className='content-centered'>
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Duo</span>
                        </Container>
                        <Message className='content-centered'>
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
                    <Grid.Row className='content-centered'>
                        <Message className='content-centered'>
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
                                violations of one or more keys or FDs. For each dataset, you'll be shown
                                various samples of the dataset, your job will be to think about
                                the key(s) or FD(s) that should reasonably hold over the dataset, given
                                the attributes and values present in the data, and mark any violations
                                of those rules you see by clicking on that cell and marking it yellow.
                            </p>
                            <p>
                                A violation could be a set of conflicting values or some other value that
                                looks wrong in the dataset given what other values correspond with it in
                                the row.
                            </p>
                            <p>
                                When you've finished giving your feedback for the sample presented to you,
                                click <strong>Next</strong> and you will be presented with another sample of
                                the dataset, and the process repeats itself. You'll have up to 15 rounds to
                                give feedback before moving on to the next dataset.
                            </p>
                            <p>
                                <strong>NOTE: </strong>
                                You do not need to worry about finding the right value for a cell. This is
                                not an error detection problem!
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
                                    <Message className='content-centered'>
                                        <Message.Header>
                                            <h2>How to Give Feedback</h2>
                                        </Message.Header>
                                        <Divider />
                                        <p>
                                            To mark a cell as a violation, click on the cell. The cell will be
                                            highlighted yellow.
                                        </p>
                                        <p>
                                            If you decide at any point that this cell is not a violation and want
                                            to undo your feedback for that cell, you can simply click on the cell
                                            again to unhighlight and unmark it.
                                        </p>
                                        <p>
                                            To submit your feedback for that round, or if you have no new feedback
                                            and simply want to see a new sample, click "Next."
                                        </p>
                                        <p>
                                            Your feedback will be visible throughout the entire interaction, i.e. if you 
                                            previously marked a cell as a violation and that tuple reappears in a sample later
                                            on, the cell will still be highlighted so that you can review your previous feedback
                                            alongside new data.
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
                                    <Message className='content-centered'>
                                        <Message.Header>
                                            <h2>Let's Review the Data You'll Be Working With</h2>
                                        </Message.Header>
                                        <Divider />
                                        <h3>Airport Data</h3>
                                        <p>
                                            These datasets describe information about various airports or airfields.
                                        </p>
                                        <h4>Attribute Definitions</h4>
                                        <p>
                                            <strong>NOTE: </strong>
                                            Depending on which dataset you're working with, you may only see a subset of these attributes.
                                        </p>
                                        <List as='ul'>
                                            <List.Item as='li'>
                                                <strong>sitenumber: </strong>The site number allocated to the airfield.
                                            </List.Item>
                                            <List.Item as='li'>
                                                <strong>type: </strong>The type of airfield.
                                            </List.Item>
                                            <List.Item as='li'>
                                                <strong>facilityname: </strong>The name of the airfield.
                                            </List.Item>
                                            <List.Item as='li'>
                                                <strong>owner: </strong>The person, group, or entity that owns the airfield.
                                            </List.Item>
                                            <List.Item as='li'>
                                                <strong>manager: </strong>The person, group, or entity that manages/oversees the day-to-day functions of the airfield.
                                            </List.Item>
                                            <strong>NOTE: </strong>Managers can manage multiple airfields, and some airfields have no manager (these are labeled "NO MANAGER").
                                        </List>
                                        <Divider />
                                        <h3>Movie Datasets</h3>
                                        <p>
                                            These datasets describe information about various English-language movies
                                            and TV shows, such as the name of the movie, its MPAA or FCC rating
                                            (e.g. PG-13, R, TV-14), the director of the movie, and the genre of the movie.
                                        </p>
                                        <h4>Attribute Definitions</h4>
                                        <p>
                                            <strong>NOTE: </strong>
                                            Depending on which dataset you're working with, you may only see a subset of these attributes.
                                        </p>
                                        <List as='ul'>
                                            <List.Item as='li'><strong>listingnumber: </strong>The database's listing number for this movie or TV show.</List.Item>
                                            <List.Item as='li'><strong>title: </strong>The name of the movie or TV show.</List.Item>
                                            <List.Item as='li'><strong>year: </strong>The year the movie or TV show was released in.</List.Item>
                                            <List.Item as='li'>
                                                <strong>rating: </strong>The content rating of the movie or TV show (e.g. PG-13, R, TV-14).
                                            </List.Item>
                                            <strong>NOTE: </strong>Some listings have not received a rating from the MPAA or FCC and are listed as "Not Rated."
                                            <List.Item as='li'><strong>director: </strong>The person who directed the movie or TV show.</List.Item>
                                            <strong>NOTE: </strong>For listings with more than one director but one person acting as the lead director, this person is listed as the director.
                                            <List.Item as='li'><strong>genre: </strong>The genre of the movie or TV show, e.g. action, drama, horror, comedy, etc.</List.Item>
                                        </List>
                                        {
                                            dataOverviewRead ? (
                                                <Message color='green'><p>Scroll Down</p></Message>
                                            ) : (
                                                <Button positive size='big' onClick={() => setDataOverviewRead(true)}>Continue</Button>
                                            )
                                        }
                                    </Message>
                                </Grid.Row>
                            </>
                        )
                    }
                    {
                        dataOverviewRead && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message className='content-centered'>
                                        <Message.Header>
                                            <h2>Let's Quickly Review FDs and Keys</h2>
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
                                        </Message>
                                        <p>
                                            For example, in a city, a building's street address (e.g. 123 Main St.) functionally determines
                                            the building's city, state, and zip code, as these three values are dependent on the address.
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
                                            For more information on FDs and to see more examples, you can go <a href='https://en.wikipedia.org/wiki/Functional_dependency#Examples' target='_blank'>here</a>.
                                        </p>
                                        <Divider />
                                        <Message info>
                                            <Message.Header>
                                                <h3>What is a key?</h3>
                                            </Message.Header>
                                            <p>
                                                A <strong>key</strong> is a special type of FD in which an attribute or set of attributes functionally determines
                                                evert other attribute in the dataset.
                                            </p>
                                        </Message>
                                        <p>
                                            For example, in a university student directory, student ID is a key, as it
                                            can be used to uniquely identify each student in the school.
                                        </p>
                                        <p>
                                            Another example of a key is a person's name and email. In a list of company
                                            employees, an employee's name and email together can uniquely identify the 
                                            individual, whereas name by itself may not be a key as multiple people can
                                            have the same name.
                                        </p>
                                        <Divider />
                                        <Message info>
                                            <Message.Header>
                                                <h3>What is a violation?</h3>
                                            </Message.Header>
                                            <p>
                                                If a tuple contains values that do not align with the rest of the dataset with
                                                respect to an FD or key (e.g. a tuple has a different value for "state" than all
                                                other tuples with same area code value), the tuple is said to be
                                                a <strong>violation</strong> of the FD or key.
                                            </p>
                                        </Message>
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
                                    <Message className='content-centered'>
                                        <Message.Header>
                                            <h2>Knowledge Check</h2>
                                        </Message.Header>
                                        <Divider />
                                        <Container>
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
                                                        label='phone'
                                                        name='q1RadioGroup'
                                                        value='phone'
                                                        checked={q1Response === 'phone'}
                                                        onChange={() => !quizDone && setQ1Response('phone')}
                                                    />
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
                                        </Container>
                                        <Divider />
                                        <Container style={{ paddingBottom: 20 }}>
                                            <p>One of the following tuples violates FD (areacode) {'=>'} state.</p>
                                            <p>Find the tuple and mark the cell with the violating value.</p>
                                            {
                                                quizDone && (
                                                    <Message positive={q2Response === q2CorrectAnswer} negative={q2Response !== q2CorrectAnswer}>
                                                        <Message.Header>
                                                            {
                                                                q2Response === q2CorrectAnswer
                                                                ? 'Correct!'
                                                                : 'Incorrect'
                                                            }
                                                        </Message.Header>
                                                        {
                                                            q2Response !== q2CorrectAnswer && (
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
                                                                            if (quizDone && q2CorrectAnswer === `${e.id}_${v}`) {
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
                                            {/* <Form>
                                                <Form.Field>
                                                    <Radio
                                                        label='2'
                                                        name='q2RadioGroup'
                                                        value='2'
                                                        checked={q2Response === '2'}
                                                        onChange={() => setQ2Response('2')}
                                                    />
                                                </Form.Field>
                                                <Form.Field>
                                                    <Radio
                                                        label='3'
                                                        name='q2RadioGroup'
                                                        value='3'
                                                        checked={q2Response === '3'}
                                                        onChange={() => setQ2Response('3')}
                                                    />
                                                </Form.Field>
                                                <Form.Field>
                                                    <Radio
                                                        label='4'
                                                        name='q2RadioGroup'
                                                        value='4'
                                                        checked={q2Response === '4'}
                                                        onChange={() => setQ2Response('4')}
                                                    />
                                                </Form.Field>
                                                <Form.Field>
                                                {
                                                        quizDone ? (
                                                            <Radio
                                                                style={{ border: '2px solid green', padding: 10 }}
                                                                label='5'
                                                                name='q2RadioGroup'
                                                                value='5'
                                                                checked={q2Response === '5'}
                                                                onChange={() => setQ2Response('5')}
                                                            />
                                                        ) : (
                                                            <Radio
                                                                label='5'
                                                                name='q2RadioGroup'
                                                                value='5'
                                                                checked={q2Response === '5'}
                                                                onChange={() => setQ2Response('5')}
                                                            />
                                                        )
                                                    }
                                                </Form.Field>
                                                <Form.Field>
                                                    <Radio
                                                        label='6'
                                                        name='q2RadioGroup'
                                                        value='6'
                                                        checked={q2Response === '6'}
                                                        onChange={() => setQ2Response('6')}
                                                    />
                                                </Form.Field>
                                            </Form> */}
                                        </Container>
                                        {
                                            quizDone ? (
                                                <Message color='green'><p>Scroll Down</p></Message>
                                            ) : (
                                                <Button positive size='big' disabled={q1Response === '' || q2Response === ''}onClick={() => setQuizDone(true)}>Submit</Button>
                                            )
                                        }
                                        {
                                            quizDone && (
                                                <>
                                                    <Divider />
                                                    <Message info>
                                                        <Message.Header>
                                                            Review your answers and the information above, and when you're ready to begin
                                                            working on your first dataset, click "I'm Ready to Begin" below.
                                                        </Message.Header>
                                                    </Message>
                                                    <Button positive size='big' onClick={handleReady}>I'm Ready to Begin!</Button>
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