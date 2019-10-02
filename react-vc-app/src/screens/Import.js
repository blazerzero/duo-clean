import React, { createRef, Component } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import {
  Button,
  Col,
  Form,
  Modal,
  Row,
  Tab,
  Tabs,
} from 'react-bootstrap';
import { connect } from 'react-redux';
import axios from 'axios';

import '../css/App.css';

class ImportButton extends Component {
  render() {
    return (
      <Route render={({ history}) => (
        <Button
          type='submit'
          variant='primary'
          onClick={() => {
            console.log('Going!');
            history.push('/results/');
          }}>
          Import
        </Button>
      )} />
    );
  }
}

class Import extends Component {
  state = {
    importedFile: null,
    showModal: false,
  }

  async _handleSubmit(history) {
    console.log(this.state.importedFile);
    if (this.state.importedFile != null) {
      const formData = new FormData();
      formData.append('file', this.state.importedFile);
      console.log(formData.get('file'));
      const config = {
        headers: {
          'content-type': 'multipart/form-data'
        }
      };
      axios.post('http://localhost:5000/import', formData, config)
        .then(response => {
          console.log(response);
          console.log(JSON.parse(response.data));
          var data = JSON.parse(response.data);
          history.push({
            pathname: '/results/',
            data: data
          });
        })
        .catch(error => console.log(error));
    }
  };

  constructor(props) {
    super(props);
  }

  _handleGetStartedClick() {
    document.getElementById('welcomeDiv').style.display = 'none';
    document.getElementById('importDiv').style.display = 'block';
  }

  _handleBackClick() {
    document.getElementById('welcomeDiv').style.display = 'block';
    document.getElementById('importDiv').style.display = 'none';
  }

  _handleModalShow = () => this.setState({ showModal: true });
  _handleModalClose = () => this.setState({ showModal: false });

  render() {

    return (
      <Route render={({ history }) => (
        <div className='site-page home'>
          <Row className='content-centered'>
            <div className='home-header'>
              <span className='home-title'>VarClean</span>
              <p className='home-subtitle'>Intelligently clean your data.</p>
            </div>
          </Row>
          <div className='body-section'>
            <div id='welcomeDiv' style={{display: 'block'}}>
              <div style={{height: '40vh'}}></div>
              <Row className='content-centered'>
                <Button
                  variant='danger'
                  className='btn-round left general-btn'
                  size='lg'
                  onClick={this._handleModalShow}>
                  LEARN MORE
                </Button>
                <Button
                  variant='primary'
                  className='btn-round right'
                  size='lg'
                  onClick={this._handleGetStartedClick}>
                  GET STARTED
                </Button>
              </Row>
            </div>
            <div id='importDiv' style={{display: 'none'}}>
              <Row className='content-centered'>
                <Button
                  variant='danger'
                  className='btn-round'
                  size='lg'
                  onClick={this._handleBackClick}>
                  BACK
                </Button>
              </Row>
              <div style={{height: '30vh'}}></div>
              <Form noValidate encType='multipart/form-data'>
                <Row className='content-centered'>
                  <Button
                    variant='primary'
                    className='btn-round left general-btn'
                    size='lg'
                    onClick={() => document.getElementById('fileUploaderHandler').click()}>
                    CHOOSE FILE
                  </Button>
                  <Button
                    variant='light'
                    className='btn-round right filename-area'
                    style={{cursor: 'default'}}
                    size='lg'>
                    {this.state.importedFile !== null ? this.state.importedFile.name : 'No file chosen'}
                  </Button>
                  <Form.Control
                    type='file'
                    placeholder='Choose a file'
                    accept='.csv'
                    className='default-file-upload'
                    id='fileUploaderHandler'
                    onChange={(e) => {
                      console.log(e.target.files);
                      this.setState({ importedFile: e.target.files[0] }, () => {
                        console.log(this.state);
                        document.getElementById('findRulesBtn').style.cursor = 'pointer';
                      });
                    }}/>
                </Row>
                <Row className='content-centered'>
                  <Button
                    variant='primary'
                    size='lg'
                    className='btn-round'
                    style={{cursor: 'default'}}
                    id='findRulesBtn'
                    disabled={this.state.importedFile === null}
                    onClick={() => this._handleSubmit(history)}>
                    FIND RULES
                  </Button>
                </Row>
              </Form>
            </div>
          </div>
          <Modal size='lg' show={this.state.showModal} onHide={this._handleModalClose}>
            <Modal.Header closeButton>
              <Modal.Title style={{ color: '#d73f09' }}>VarClean</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <Tabs defaultActiveKey="whatIs" id="uncontrolled-tab-example">
                <Tab eventKey="whatIs" title="What is VarClean?" className="modalText">
                  VarClean is a collaborative and personalized data cleaning platform. Unlike many existing data cleaning applications, VarClean learns about the true context and meaning of your dataset by leveraging your feedback to its suggestions while determining which rules to apply to the dataset. This allows VarClean to help guide you in the right direction regarding how to most effectively clean your dataset.
                </Tab>
                <Tab eventKey="howDoesWork" title="How does VarClean work?" className="modalText">
                  VarClean cleans your dataset using an interactive two-step process: optimal rule discovery and repair configuration. First, VarClean runs DFD, a functional dependency discovery algorithm, to discover a complete list of minimal functional dependencies that could potentially be applied to the dataset. It then leverages its initial knowledge of how well the dependencies fit the dataset as-is to suggest dependencies. Then, you can respond with which suggestions match your understanding of the context of the dataset, create a new rule, or modify one of the suggestions. VarClean then recalculates the fit of each dependency by analysing your feedback, and it generates a new list of suggestions. This process repeats until you have found the set of rules that you believe best fit the dataset.
                  Once you have your list of optimal rules, VarClean analyzes your picks and determines the best order in which to apply the rules to the dataset. You can follow its suggestion or build your own order of operations. Lastly, VarClean cleans the dataset based on the defined order of operations.
                </Tab>
              </Tabs>
            </Modal.Body>
          </Modal>
        </div>
      )} />

    );
  }
}

/*const mapStateToProps = (state) => {
  console.log(state);
  return {
    uploadedFile: state.importReducer.uploadedFile,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    importFile: (payload) => dispatch({
      type: 'IMPORT_FILE',
      payload: payload
    }),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(Import);*/
export default Import;
