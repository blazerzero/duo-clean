import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import {
  Button,
  Form,
  Modal,
  Row,
  Tab,
  Tabs,
} from 'react-bootstrap';

export default class Welcome extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            showModal: false,
        }
    }

    _handleModalShow = () => this.setState({ showModal: true });
    _handleModalClose = () => this.setState({ showModal: false });

    render() {
        return (
            <div>
                <Button size='lg' className='duo-btn round bvr-orange box-blur' onClick={this._handleModalShow}>LEARN MORE</Button>
                <Modal size='lg' show={this.state.showModal} onHide={this._handleModalClose}>
                    <Modal.Header closeButton>
                    <Modal.Title style={{ color: '#d73f09' }}>DuoClean</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                    <Tabs defaultActiveKey="whatIs" id="uncontrolled-tab-example">
                        <Tab eventKey="whatIs" title="What is DuoClean?" className="modalText">
                        DuoClean is an iterative and collaborative data cleaning platform.
                        Unlike many existing data cleaning applications, DuoClean directly uses the repairs you make
                        to build a cohesive list of candidate rules to apply to the dataset and intelligently decide
                        what parts of your dataset are important to analyze next.
                        </Tab>
                        <Tab eventKey="howDoesWork" title="How does DuoClean work?" className="modalText">
                        DuoClean cleans your dataset using an interactive three-step process:
                        optimal rule discovery, learning-based cleaning, and intelligent data sampling.
                        All you have to worry about is cleaning the sample of your data that's shown to you. DuoClean
                        directly analyzes the repairs you submit to iteratively build a list of possible rules to apply
                        to the dataset as a whole. It then selects rules to apply based on the repairs you submitted and
                        how well rules have performed in the past, reinforcing rules that are particularly effective.
                        Then, it analyzes the history of each cell in the dataset to decide which tuples you should
                        review next.
                        </Tab>
                    </Tabs>
                    </Modal.Body>
                </Modal>
            </div>
        );
    }

}