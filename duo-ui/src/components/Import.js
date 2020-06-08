import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import {
    Button,
    Form,
    Row,
} from 'react-bootstrap';
import history from '../history';
import axios from 'axios';

import '../global';

export default class Import extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            importedFile: null,
            projectId: '',
        }
    }

    _handleSubmit = () => {
        // Connect to backend
        if (this.state.importedFile != null) {
            const formData = new FormData();
            formData.append('file', this.state.importedFile);
            console.log(formData.get('file'));
            const config = {
                headers: {
                    'content-type': 'multipart/form-data'
                }
            };
            axios.post(global.API.concat('/import'), formData, config)
                .then(response => {
                    var { header, project_id, msg } = JSON.parse(response.data);
                    console.log(msg);
                    history.push({
                        pathname: '/duo/project',
                        header,
                        project_id,
                    })
                })
                .catch(error => console.log(error));
            {/* history.push({
                pathname: '/duo/project'.concat(this.state.projectId),
            });*/ }
        }
    }

        render() {
            return (
                <div style={{ marginTop: '2em' }}>
                    <Form noValidate encType='multipart/form-data'>
                        <Row className='content-centered'>
                            <Button
                                variant='primary'
                                className='duo-btn round box-blur'
                                size='lg'
                                onClick={() => document.getElementById('fileUploaderHandler').click()}>
                                CHOOSE FILE
                        </Button>
                        </Row>
                        <Row className='content-centered'>
                            <Button
                                variant='light'
                                className='duo-btn round box-blur'
                                style={{ cursor: 'default' }}
                                size='lg'>
                                {this.state.importedFile !== null ? this.state.importedFile.name : 'No file chosen'}
                            </Button>
                            <Form.Control
                                type='file'
                                placeholder='Choose a file'
                                accept='.csv'
                                style={{ display: 'none' }}
                                id='fileUploaderHandler'
                                onChange={(e) => {
                                    console.log(e.target.files);
                                    this.setState({ importedFile: e.target.files[0] });
                                }} />
                        </Row>
                        <Row className='content-centered'>
                            {this.state.importedFile !== null && <Button
                                variant='primary'
                                size='lg'
                                className='duo-btn round box-blur'
                                id='findRulesBtn'
                                onClick={this._handleSubmit}>
                                START CLEANING
                        </Button>}
                        </Row>
                    </Form>
                </div>
            );
        }

    }