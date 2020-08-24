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
      scenarioID: null,
      participantName: null,
      isProcessing: false,
    }
  }

  _handleSubmit = async(history) => {
    if (!isNaN(this.state.scenarioID) || this.state.participantName.length === 0) {
      this.setState({ isProcessing: true });
      const formData = new FormData();
      formData.append('scenario_id', this.state.scenarioID);
      formData.append('participant_name', this.state.participantName);
      console.log(formData.get('file'));
      const config = {
        headers: {
          'content-type': 'multipart/form-data'
        }
      };
      axios.post('http://167.71.155.153:5000/duo/api/import', formData, config)
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
            scenario_desc
          });
        })
        .catch(error => console.log(error));
    } else {
      alert('Please make sure you\'ve entered your name and an integer scenario ID.');
    }
  };

  _handleScenarioIDChange = (event) => {
    console.log(event.target.value);
    var scenarioID = event.target.value;
    this.setState({ scenarioID });
  }

  _handleNameChange = (event) => {
    console.log(event.target.value);
    var participantName = event.target.value;
    this.setState({ participantName });
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
          <div className='body-section'>
            <div id='importDiv'>
              <div style={{height: '30vh'}}></div>
              <Form noValidate encType='multipart/form-data'>
                <Row className='content-centered small'>
                  <InputGroup>
                    <InputGroup.Prepend>
                      <InputGroup.Text>Name: </InputGroup.Text>
                    </InputGroup.Prepend>
                    <Form.Control
                      type='text'
                      aria-label='Enter your name.'
                      required
                      feedback='You must enter your name.'
                      onChange={this._handleNameChange}
                      />
                  </InputGroup>
                </Row>
                <Row className='content-centered small'>
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
