import React, { createRef, Component } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import {
  Button,
  Col,
  Form,
  Row,
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
          var res = JSON.parse(response.data);
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

  render() {
    return (
      <Route render={({ history }) => (
        <div className='home'>
          <Row className='content-centered'>
            <div className='home-header'>
              <span className='home-title'>VarClean</span>
              <p className='home-subtitle'>Intelligently clean your data.</p>
            </div>
          </Row>
          <div className='body-section'>
            <div id='welcomeDiv' style={{display: 'block'}}>
              <Row className='content-centered'>
                <Button
                  variant='info'
                  className='btn-round left'
                  size='lg'>
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
              <Form noValidate encType='multipart/form-data'>
                <Row className='content-centered'>
                  <Button
                    variant='info'
                    className='btn-round left'
                    size='lg'
                    onClick={() => document.getElementById('fileUploaderHandler').click()}>
                    CHOOSE FILE
                  </Button>
                  <Button
                    variant='light'
                    className='btn-round right filename-area'
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
