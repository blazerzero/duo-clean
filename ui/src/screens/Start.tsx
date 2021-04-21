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
    Input,
    Checkbox
} from 'semantic-ui-react'
import server from '../utils/server'
import logo from '../images/OSU_horizontal_2C_O_over_B.png'

interface StartProps {}

export const Start: FC<StartProps> = () => {

    const history = useHistory()
    const location = useLocation()
    const { email, scenarios } = location.state as any

    const [processing, setProcessing] = useState<boolean>(false)
    const [interfaceGuideRead, setInterfaceGuideRead] = useState<boolean>(false)
    const [dataOverviewRead, setDataOverviewRead] = useState<boolean>(false)
    const [fdReviewRead, setFDReviewRead] = useState<boolean>(false)
    const [quizQ1Done, setQuizQ1Done] = useState<boolean>(false)
    const [quizFullDone, setQuizFullDone] = useState<boolean>(false)
    const [quizAnswersReviewed, setQuizAnswersReviewed] = useState<boolean>(false)
    const [header, setHeader] = useState<string[]>([])
    const [fd, setFD] = useState<{[key: string]: string}>({})
    const [doesntKnowFD, setDoesntKnowFD] = useState<boolean>(false)

    const [q1Response, setQ1Response] = useState<string>('')
    const q1CorrectAnswer = 'name'
    const [q2Response, setQ2Response] = useState<string>('')
    const q2CorrectAnswers = ['4_305', '6_305', '4_FL', '6_CA']
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
        setQuizFullDone(true)
        setHeader(response.data.header)
        setProcessing(false)
    }

    const handleReady = async () => {
        setProcessing(true)
        const first_scenario: number = scenarios.splice(0, 1) as number
        const lhs: string[] = Object.keys(fd).filter((k: string) => fd[k] === 'LHS')
        lhs.sort()
        const rhs: string[] = Object.keys(fd).filter((k: string) => fd[k] === 'RHS')
        rhs.sort()
        const initial_fd: string = `(${lhs.join(', ')}) => ${rhs.join(', ')}`
        console.log(initial_fd)
        const response: AxiosResponse = await server.post('/import', {
            email,
            scenario_id: first_scenario.toString(),
            initial_fd,
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

    const isValidFD = () => {
        return Object.keys(fd).filter((k: string) => fd[k] === 'LHS').length > 0
        && Object.keys(fd).filter((k: string) => fd[k] === 'RHS').length > 0
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
            state: 'OR',
            zip: 97007
        },
        {
            name: 'Nate',
            areacode: 206,
            state: 'WA',
            zip: 98802
        },
        {
            name: 'Leilani',
            areacode: 808,
            state: 'HI',
            zip: 96850
        },
        {
            name: 'Tobias',
            areacode: 541,
            state: 'OR',
            zip: 97401
        },
        {
            name: 'Samantha',
            areacode: 206,
            state: 'WA',
            zip: 43153
        },
        {
            name: 'Tobias',
            areacode: 541,
            state: 'OR',
            zip: 97401
        },
    ]

    const q2Data = [
        {
            id: 1,
            name: 'Darrell',
            areacode: 775,
            state: 'NV',
            zip: 89501
        },
        {
            id: 2,
            name: 'Henry',
            areacode: 404,
            state: 'GA',
            zip: 30334
        },
        {
            id: 3,
            name: 'Blake',
            areacode: 775,
            state: 'NV',
            zip: 89501
        },
        {
            id: 4,
            name: 'Jusuf',
            areacode: 305,
            state: 'FL',
            zip: 33130
        },
        {
            id: 5,
            name: 'Shania',
            areacode: 775,
            state: 'NV',
            zip: 89501
        },
        {
            id: 6,
            name: 'Ellen',
            areacode: 305,
            state: 'CA',
            zip: 33128
        },
    ]

    return (
        <Dimmer.Dimmable as={Segment} dimmed={processing}>
            <Grid centered stretched={false} columns={1} className='site-page home'>
                <Grid.Column>
                    <Divider />
                    <Grid.Row className='content-centered'>
                        <Container className='section' style={{ backgroundColor: 'white', position: 'absolute', top: 0, right: 0, width: '10vw', maxWidth: '500px', height: '8vh', borderBottomLeftRadius: 20 }} >
                            <img src={logo} style={{ padding: 10, position: 'absolute', top: 0, right: 0, width: '100%', height: 'auto' }} alt='OSU logo' />
                        </Container> 
                        <Container className='home-header box-blur'>
                            <span className='home-title'>Discovering Rules and Patterns in Data</span>
                        </Container>
                    </Grid.Row>
                    <Grid.Row>
                        <Message>
                            <Message.Header>
                                <h2>Let's Review Functional Dependencies</h2>
                            </Message.Header>
                            <Divider />
                            <Message info>
                                <Message.Header>
                                    <h3>What is an FD?</h3>
                                </Message.Header>
                                <p>
                                    A <strong>functional dependency</strong>, or <strong>FD</strong>, is a rule 
                                    that explains how attributes in a dataset are dependent on each other.
                                </p>
                            </Message>
                            <p>
                                For example, in the dataset below, a building's city and zip code functionally determine
                                the state that building is in. This rule is represented by the expression <strong>{'(city, zip) => state'}</strong>.
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
                                                    Object.entries(e).map(([k, v], i) => k !== 'id' && (
                                                        <Table.Cell key={i}>{v}</Table.Cell>
                                                    ))
                                                }
                                            </Table.Row>
                                        ))
                                    }
                                </Table.Body>
                            </Table>
                            <Message warning>
                                <Message.Header>
                                    <h4>Some FDs functionally determine only one attribute, while others determine many attributes.</h4>
                                </Message.Header>
                                <p>
                                    E.g. area code only determines state, but ID determines all attributes. These are respectfully written
                                    as <strong>{'(areacode => state)'}</strong> and <strong>{'(id) => address, city, state, zip'}</strong>.
                                </p>
                            </Message>
                            <Message warning>
                                <Message.Header>
                                    <h4>
                                        The attributes that functionally determine other attributes are collectively called the left-hand side (LHS) of the rule,
                                        while the attributes that are dependent on the left-hand side are collectively called the right-hand side (RHS) of the rule.
                                    </h4>
                                </Message.Header>
                                <p>
                                    E.g. in the rule <strong>{'(city, zip) => state'}</strong>, city and zip collectively form the LHS and state forms the RHS.
                                    In the rule <strong>{'(id) => address, city, state, zip'}</strong>, id forms the LHS and address, city, state, and zip collectively form the RHS.
                                </p>
                            </Message>
                            <p>
                                For more information on FDs and to see more examples, you can go <a href='https://en.wikipedia.org/wiki/Functional_dependency#Examples' target='_blank' rel='noopener noreferrer'>here</a>.
                            </p>
                            <Divider />
                            <Message info>
                                <Message.Header>
                                    <h3>What is an exception to a rule?</h3>
                                </Message.Header>
                                <p>
                                    If a cell in a tuple has a value that does not align with the rest of the dataset with
                                    respect to an FD, the cell is said to be part of a <strong>exception</strong> to the rule.
                                </p>
                            </Message>
                            {/* UPDATE THIS */}
                            <p>
                                Let's see the same dataset again. Here, the two tuples with the address "800 6th Ave"
                                have a exception to the FD <strong>{'(city, zip) => state'}</strong> present in the state attribute (these have been highlighted below),
                                as two places with the same city and ZIP code have different states listed.
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
                                                        (e.id === 3 || e.id === 6) && k === 'state' ? (
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
                    {
                        fdReviewRead && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message>
                                        <Message.Header>
                                            <h2>Quiz</h2>
                                        </Message.Header>
                                        <Divider />
                                        <p>In the following table, which of the following rule holds strongest over this dataset?</p>
                                        {
                                            quizFullDone && (
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
                                                    label='areacode determines all other attributes'
                                                    name='q1RadioGroup'
                                                    value='areacode'
                                                    checked={q1Response === 'areacode'}
                                                    onChange={() => !quizFullDone && setQ1Response('areacode')}
                                                />
                                            </Form.Field>
                                            <Form.Field>
                                                {
                                                    quizFullDone ? (
                                                        <Radio
                                                            style={{ border: '2px solid green', padding: 10 }}
                                                            label='name determines all other attributes'
                                                            name='q1RadioGroup'
                                                            value='name'
                                                            checked={q1Response === 'name'}
                                                            onChange={() => !quizFullDone && setQ1Response('name')}
                                                        />
                                                    ) : (
                                                        <Radio
                                                            label='name determines all other attributes'
                                                            name='q1RadioGroup'
                                                            value='name'
                                                            checked={q1Response === 'name'}
                                                            onChange={() => !quizFullDone && setQ1Response('name')}
                                                        />
                                                    )
                                                }
                                            </Form.Field>
                                            <Form.Field>
                                                <Radio
                                                    label='areacode and state determine all other attributes'
                                                    name='q1RadioGroup'
                                                    value='combo'
                                                    checked={q1Response === 'combo'}
                                                    onChange={() => !quizFullDone && setQ1Response('combo')}
                                                />
                                            </Form.Field>
                                            <Form.Field>
                                                <Radio
                                                    label='zip determines all other attributes'
                                                    name='q1RadioGroup'
                                                    value='zip'
                                                    checked={q1Response === 'zip'}
                                                    onChange={() => setQ1Response('zip')}
                                                />
                                            </Form.Field>
                                        </Form>
                                        <Divider />
                                        {
                                            quizQ1Done ? (
                                                <Message color='green'><p>Scroll Down</p></Message>
                                            ) : (
                                                <Button positive size='big' disabled={q1Response === ''} onClick={() => setQuizQ1Done(true)}>Next</Button>
                                            )
                                        }
                                        { 
                                            quizQ1Done && (
                                                <>
                                                    <Divider />
                                                    <p>The table below contains an exception to the rule <strong>{'(areacode) => state'}.</strong></p>
                                                    <p>Find the exception and mark one of the cells whose value is causing the exception.</p>
                                                    {
                                                        quizFullDone && (
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
                                                                Object.keys(q2Data[0]).map((h: string) => h !== 'id' && (
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
                                                                                Object.entries(e).filter(([k, v], i) => k !== 'id').map(([k, v], i) => {
                                                                                    if (quizFullDone && q2CorrectAnswers.includes(`${e.id}_${v}`)) {
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
                                                                                                    if (!quizFullDone) {
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
                                                                                                    if (!quizFullDone) {
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
                                                        quizFullDone ? (
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
                                                </>
                                            )
                                        }
                                        
                                    </Message>
                                </Grid.Row>
                            </>
                        )
                    }
                    {
                        quizFullDone && quizAnswersReviewed && (
                            <>
                                <Divider />
                                <Grid.Row>
                                    <Message>
                                        <Message.Header>
                                            <h2>How to Interact With the Datasets</h2>
                                        </Message.Header>
                                        <Divider />
                                        <p>
                                            To mark a cell as part of a exception to a rule, click on the cell. The cell will be
                                            highlighted yellow.
                                        </p>
                                        <p>
                                            If you decide at any point that this cell is not part of an exception and want
                                            to undo your feedback for that cell, you can simply click on the cell
                                            again to unhighlight and unmark it.
                                        </p>
                                        <p>
                                            To submit your marks for that round, click "Next" and let us know what rule you're most confident
                                            holds over the dataset given what you've seen so far, and you'll be
                                            presented with a new sample from the dataset. If you don't see anything that should be marked,
                                            you don't have to mark anything, and you can just respond to the prompt to get a fresh sample.
                                        </p>
                                        <p>
                                            Your feedback will be visible throughout the entire interaction, i.e. if you 
                                            previously marked a cell as part of an exception and that tuple reappears in a sample later
                                            on, the cell will still be highlighted so that you can review and change your
                                            previous feedback alongside new data.
                                        </p>
                                        <p>
                                            You'll have up to 15 rounds to give feedback before moving on to the next dataset.
                                        </p>
                                        <p>
                                            One round is defined as giving feedback by marking any cells you believe are part
                                            of exceptions, clicking "Next," and letting us know what you think is the strongest rule
                                            over the data given everything you've seen so far.
                                        </p>
                                        <p>
                                            After 6 rounds, if you have no more feedback left to give for the dataset or are otherwise
                                            done giving feedback, answer the prompt at the bottom one last time and click "I'm All Done" to finish working with the dataset.
                                        </p>
                                        <p>
                                            <strong>NOTE: </strong>
                                            You do not need to worry about knowing or finding the right value for a cell! This is
                                            not an error detection problem. Your goal is just to discover rules and find exceptions to them.
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
                                        <Message>
                                            <Message.Header>
                                                <h3>
                                                    This dataset has the following attributes: [{header.join(', ')}]. Given this
                                                    schema, what rule are you most confident holds over this dataset?
                                                </h3>
                                            </Message.Header>
                                            <p>E.g. {'(facilityname) => type, owner'}; {'(title, year) => director'}</p>
                                            <h4>Answer by indicating, for each attribute below, whether the attribute is part of the left-hand side or right-hand side of the rule, or not part of the rule.</h4>
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
                                                    <div style={{ flexDirection: 'row', paddingBottom: 10 }}>
                                                        <h4>{h}</h4>
                                                        <Radio
                                                            style={{ padding: 10 }}
                                                            label='Left-hand side'
                                                            name={`${h}_radioGroup`}
                                                            value='LHS'
                                                            checked={fd[h] === 'LHS'}
                                                            onChange={() => {
                                                                const newFD: {[key: string]: string} = {}
                                                                Object.keys(fd).forEach((h: string) => newFD[h] = fd[h])
                                                                console.log(newFD)
                                                                newFD[h] = 'LHS'
                                                                console.log(newFD)
                                                                setFD(newFD)
                                                            }}
                                                        />
                                                        <Radio
                                                            style={{ padding: 10 }}
                                                            label='Right-hand side'
                                                            name={`${h}_radioGroup`}
                                                            value='RHS'
                                                            checked={fd[h] === 'RHS'}
                                                            onChange={() => {
                                                                const newFD: {[key: string]: string} = {}
                                                                Object.keys(fd).forEach((h: string) => newFD[h] = fd[h])
                                                                console.log(newFD)
                                                                newFD[h] = 'RHS'
                                                                console.log(newFD)
                                                                setFD(newFD)
                                                            }}
                                                        />
                                                        <Radio
                                                            style={{ padding: 10 }}
                                                            label='Not part of the rule'
                                                            name={`${h}_radioGroup`}
                                                            value='N/A'
                                                            checked={fd[h] === 'N/A'}
                                                            onChange={() => {
                                                                const newFD: {[key: string]: string} = {}
                                                                Object.keys(fd).forEach((h: string) => newFD[h] = fd[h])
                                                                console.log(newFD)
                                                                newFD[h] = 'N/A'
                                                                console.log(newFD)
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
                                                            When you're ready to begin interacting with the dataset, click "Go to the Data" below.
                                                        </Message.Header>
                                                    </Message>
                                                    <Button positive size='big' onClick={handleReady}>Go to the Data</Button>
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