import React, { Component } from 'react';
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

  render() {
    return (
      <Route render={({ history }) => (
        <div className='body-section home'>
          <Form noValidate encType='multipart/form-data'>
            <Row className='content-centered'>
              <div className='upload-btn-wrapper'>
                <Button
                  variant='info'
                  className='btn-round'
                  size='lg'>
                  Upload a file
                </Button>
                <input type='file' name='myfile' />
              </div>
            </Row>
            <Row className='content-centered'>
              <Button
                variant='primary'
                size='lg'
                className='btn-round'
                onClick={() => this._handleSubmit(history)}>
                Import
              </Button>
            </Row>
          </Form>
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
