import React, { Component } from 'react';
import { Route } from 'react-router-dom';
import {
  Button,
  Form,
  Modal,
  Row,
  InputGroup,
  Spinner,
} from 'react-bootstrap';
import axios from 'axios';

class Import extends Component {

  constructor(props) {
    super(props);

    this.state = {
      scenarioID: '',
      projectID: '',
      isProcessing: false,
      name: ''
    }
  }

  _handleSubmit = async(history) => {
    if ((this.state.scenarioID.length > 0 && this.state.name.length > 0) && this.state.projectID.length === 0) {
      this.setState({ isProcessing: true });
      const formData = new FormData();
      formData.append('name', this.state.name);
      formData.append('scenario_id', this.state.scenarioID);
      axios.post('http://167.71.155.153:5000/duo/api/import', formData)
        .then(response => {
          this.setState({ isProcessing: false });
          var { header, project_id, msg, scenario_desc } = JSON.parse(response.data);
          console.log(msg);
          alert('Your Project ID is '.concat(project_id, '. This will be visible to you while you\'re working, but please make sure to write it down as well.'));
          history.push({
            pathname: '/duo/clean/',
            header,
            project_id,
            scenario_id: this.state.scenarioID,
            scenario_desc,
            is_resuming: false,
            sample: null,
            true_pos: 0,
            false_pos: 0,
            feedback: null
          });
        })
        .catch(error => console.log(error));
    } else if (this.state.projectID.length > 0 && (this.state.scenarioID.length === 0 && this.state.name.length === 0)) {
      this.setState({ isProcessing: true });
      const formData = new FormData();
      formData.append('project_id', this.state.projectID);
      axios.post('http://167.71.155.153:5000/duo/api/resume', formData)
        .then(response => {
          this.setState({ isProcessing: false });
          var { header, msg, scenario_id, scenario_desc, sample, true_pos, false_pos, feedback } = JSON.parse(response.data);
          console.log(msg);
          if (msg === '[DONE]') {
            alert('You have already completed this interaction!');
          } else if (msg === '[INVALID PROJECT ID]') {
            alert('The project ID you entered could not be found in the system. Make sure you\'ve entered your project ID correctly.');
          } else {
            alert('Welcome back! Let\'s get back to it!');
            history.push({
              pathname: '/duo/clean/',
              header,
              project_id: this.state.projectID,
              scenario_id,
              scenario_desc,
              is_resuming: true,
              sample,
              true_pos,
              false_pos,
              feedback
            });
          }
        })
        .catch(error => console.log(error));
    } else {
      alert('Please make sure you\'ve filled out the form correctly.');
    }
  };

  _handleNameChange = (event) => {
    console.log(event.target.value);
    var name = event.target.value;
    this.setState({ name });
  }

  _handleScenarioIDChange = (event) => {
    console.log(event.target.value);
    var scenarioID = event.target.value;
    this.setState({ scenarioID });
  }

  _handleProjectIDChange = (event) => {
    console.log(event.target.value);
    var projectID = event.target.value;
    this.setState({ projectID });
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page home'>
          <Modal show={this.state.isProcessing} animation={false} backdrop='static'>
            <Modal.Body>
              <p><strong>Processing...</strong></p>
              <Spinner animation='border' />
            </Modal.Body>
          </Modal>
          <Row className='content-centered'>
            <div className='home-header box-blur'>
              <span className='home-title'>Duo</span>
            </div>
          </Row>
          <div className='body-section content-centered'>
            <div id='importDiv'>
              <div style={{height: '10vh'}}></div>
              <Form noValidate encType='multipart/form-data'>
                <Row className='content-centered'>
                  <div className='home-header box-blur'>
                    <span>IF YOU'RE STARTING A NEW INTERACTION</span>
                  </div>
                </Row>
                <Row className='content-centered small'>
                  <InputGroup>
                    <InputGroup.Prepend>
                      <InputGroup.Text>Name: </InputGroup.Text>
                    </InputGroup.Prepend>
                    <Form.Control
                      type='text'
                      aria-label='Enter your name here.'
                      required
                      feedback='You must enter your name.'
                      onChange={this._handleNameChange}
                      />
                  </InputGroup>
                  <InputGroup>
                    <InputGroup.Prepend>
                      <InputGroup.Text>Scenario ID: </InputGroup.Text>
                    </InputGroup.Prepend>
                    <Form.Control
                      type='text'
                      aria-label='Enter scenario ID here.'
                      required
                      feedback='You must enter a scenario ID.'
                      onChange={this._handleScenarioIDChange}
                      />
                  </InputGroup>
                </Row>
                <Row className='content-centered'>
                  <div className='home-header box-blur'>
                    <span>OR, IF YOU'RE RETURNING TO AN INTERACTION</span>
                  </div>
                </Row>
                <Row className='content-centered small'>
                  <InputGroup>
                    <InputGroup.Prepend>
                      <InputGroup.Text>Existing Project ID: </InputGroup.Text>
                    </InputGroup.Prepend>
                    <Form.Control
                      type='text'
                      aria-label='Enter scenario ID here.'
                      required
                      feedback='Should be an 8-digit number with some leading zeroes.'
                      onChange={this._handleProjectIDChange}
                      />
                  </InputGroup>
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
                    SUBMIT
                  </Button>
                </Row>
              </Form>
            </div>
          </div>
        </div>
      )} />

    );
  }
}

export default Import;
