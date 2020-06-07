import React, { Component } from 'react';
// import Table from '../components/Table';
import Header from '../components/Header';
import {
    Alert,
    Button,
    Form,
    Modal,
    Row,
    Col,
    Table,
} from 'react-bootstrap';
import axios from 'axios';
import { join, pick } from 'lodash';

import '../global';

export default class Project extends Component {

    constructor(props) {
        super(props);
        this.state = {
            header: [],
            data: [],
            changeMap: [],
            project_id: null,
            isModalOpen: false,
            modalCellValue: null,
            modalCellKey: null,
        }
    }

    _handleSubmitFeedback = async() => {
        const formData = new FormData();
        formData.append('project_id', this.state.project_id);
        formData.append('data', JSON.stringify(this.state.data));
        formData.append('sample_size', 10);
        axios.post(global.API.concat('/clean'), formData)
            .then(async(response) => {
                var res = JSON.parse(response.data);
                var { sample, changes, msg } = pick(res, ['sample', 'changes', 'msg']);
                changes = JSON.parse(changes);
                var changeMap = await this._buildChangeMap(data, changes);
                this.setState({
                    data: sample,
                    changeMap
                });
            })
            .catch(error => {
                console.log(error);
            })
    }

    _handleCellModelOpen = async(key, event) => {
        var pieces = key.split('_');
        var idx = parseInt(pieces.shift());
        var attr = pieces.join('_');
        this.setState({
            isModalOpen: true,
            modalCellKey: key,
            modalCellValue: this.state.data[idx][attr],
        });
    }

    _handleCellModalClose = async() => {
        this.setState({
            isModalOpen: false,
            modalCellKey: null,
            modalCellValue: null,
        });
    }

    _handleChangeSave = async() => {
        
    }

    _handleDone = () => {
        alert('Thank you for participating! Please revisit your instructions for next steps.');
    }

    _getSampleData = async(project_id, sample_size) => {
        const formData = new FormData();
        formData.append('project_id', project_id);
        formData.append('sample_size', sample_size);
        axios.post(global.API.concat('/sample'), formData)
            .then(async(response) => {
                var res = JSON.parse(response.data);
                var { sample, changes, msg } = pick(res, ['sample', 'changes', 'msg']);
                changes = JSON.parse(changes);
                var changeMap = this._buildChangeMap(sample, changes);
                this.setState({
                    data: sample,
                    changeMap
                });
            })
            .catch(error => {
                console.log(error);
            })
    }

    _buildChangeMap = async(data, changes) => {
        var changeMap = {};
        var rows = Object.keys(data);
        var cols = this.state.header;
        for (var i = 0; i < rows.length; i++) {
            var tup = {};
            for (var j = 0; j < cols.length; j++) {
                var cell = changes.find(e => e.row === parseInt(rows[i]) && e.col === cols[j]);
                tup[cols[j]] = cell.repaired;
            }
            changeMap[rows[i]] = tup;
        }
        return changeMap;
    }

    _renderHeader = async() => {
        return this.state.header.map((item, idx) = <th key={'header_'.concat(idx)}>{item}</th>);
    }

    componentDidMount() {
        const { header, project_id } = this.props.location;
        this.setState({ header, project_id }, async() => {
            await this._getSampleData(this.state.project_id, this.state.sample_size);
        });
    }

    render() {
        return (
            <div className='content-centered site-page'>
                <Modal show={this.state.isModalOpen} onHide={this._handleCellModalClose} animation={false}>
                    <Form onSubmit={this._handleChangeSave}>
                        <Modal.Header closeButton>
                            <Modal.Title>Edit Cell</Modal.Title>
                        </Modal.Header>
                        <Modal.Body>
                            <Form.Group>
                                <Form.Label><strong>Current Value; </strong>{this.state.modalCellValue}</Form.Label>
                            </Form.Group>
                            <Form.Group>
                                <Form.Lavel><strong>New Value: </strong></Form.Lavel>
                                <Form.Control defaultValue={this.state.modalCellValue} />
                            </Form.Group>
                        </Modal.Body>
                        <Modal.Footer>
                            <Button variant='secondary' className='duo-btn round' onClick={this._handleCellModalClose}>
                                Cancel
                            </Button>
                            <Button className='duo-btn round bvr-orange' type='submit'>
                                Save
                            </Button>
                        </Modal.Footer>
                    </Form>
                </Modal>
                <Header projectId='TBD'/>
                <Row>
                    <Col>
                        <Alert variant='success' style={{border: '1px black solid'}}>Green cells indicate cells that<br/>the system repaired.</Alert>
                    </Col>
                    <Col>
                        <Alert variant='warning' style={{border: '1px black solid'}}>Yellow cells indicate cells in which <br/>contradicting values occurred while the system<br/>was repairing the dataset.</Alert>
                    </Col>
                </Row>
                <div>
                    <Table bordered responsive>
                        <thead>
                            <tr>
                                <th>Noisy Tuple?</th>
                                { this._renderHeader }
                            </tr>
                        </thead>
                        <tbody>
                            { Object.keys(this.state.data).map((i) => {
                                return (
                                    <tr key={i}>
                                        { Object.keys(this.state.data[i]).map((j) => {
                                            var key = i.toString().concat('_', j);
                                            return (
                                                <td
                                                    key={key} style={{cursor: 'pointer', backgroundColor: (this.state.changeMap[i][j] ? '#FFF3CD' : 'white')}}
                                                    onClick={this._handleCellClick.bind(this, key)}>
                                                    {this.state.data[i][j]}
                                                </td>
                                            )
                                        })}
                                    </tr>
                                )
                            })}
                        </tbody>
                    </Table>
                </div>
                <div>
                    <Button
                        className='duo-btn round bvr-orange box-blur'
                        size='lg'
                        onClick={this._handleSubmit}>
                        SUBMIT CHANGES AND SEE NEW EXAMPLES
                    </Button>
                </div>
            </div>
        )
    }
}