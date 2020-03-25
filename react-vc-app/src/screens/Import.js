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
import axios from 'axios';

import '../css/App.css';

class Import extends Component {
  state = {
    importedFile: null,
    showModal: false,
  }

  async _handleSubmit(history) {
    if (this.state.importedFile != null) {
      const formData = new FormData();
      formData.append('file', this.state.importedFile);
      console.log(formData.get('file'));
      const config = {
        headers: {
          'content-type': 'multipart/form-data'
        }
      };
      axios.post('http://167.71.155.153:5000/duo/api/import', formData, config)
        .then(response => {
          var { header, project_id, msg } = JSON.parse(response.data);
          console.log(msg);
          alert('Your Project ID is '.concat(project_id, '. This will be visible to you while you\'re working, but please write down your Project ID.'));
          history.push({
            pathname: '/results/',
            header: header,
            project_id: project_id
          });
        })
        .catch(error => console.log(error));
    }
  };

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
            <div className='home-header box-blur'>
              <span className='home-title'>DuoClean</span>
              <p className='home-subtitle'>Intelligently clean your data.</p>
            </div>
          </Row>
          <div className='body-section'>
            <div id='welcomeDiv' style={{display: 'block'}}>
              <div style={{height: '40vh'}}></div>
              <Row className='content-centered'>
                <Button
                  variant='danger'
                  className='btn-round left general-btn box-blur'
                  size='lg'
                  onClick={this._handleModalShow}>
                  LEARN MORE
                </Button>
                <Button
                  variant='primary'
                  className='btn-round right box-blur'
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
                  className='btn-round box-blur'
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
                    className='btn-round left general-btn box-blur'
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
                    className='default-file-upload box-blur'
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
                    className='btn-round box-blur'
                    style={{cursor: 'default'}}
                    id='findRulesBtn'
                    disabled={this.state.importedFile === null}
                    onClick={() => this._handleSubmit(history)}>
                    START CLEANING
                  </Button>
                </Row>
              </Form>
            </div>
          </div>
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
