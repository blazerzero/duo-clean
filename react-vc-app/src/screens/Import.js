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
      /*const formData = new FormData();
      formData.set('file', this.state.importedFile);
      axios.post('http://localhost:5000/import', formData).then(res => {
        console.log(res);
      }).catch(error => console.log(error));*/
      /*let response = await fetch('http://localhost:5000/import', {
        method: 'POST',
        headers: {
          Accept: 'multipart/form-data',
          'Content-Type': 'multipart/form-data',
        },
        body: data
      });*/
      //console.log('done fetching!');
      //setTimeout(function() {history.push('/results/', { data: response })}, 3000);
      //axios.post('http://localhost:5000/import', data)
        //.then(response => history.push('/results/', { data: response }))
        //.catch(error => console.log("POST error:", error));
      //history.push('/results/', {test: 'success'});
    }
  };

  render() {
    return (
      <Route render={({ history }) => (
        <div className="body-section">
          <Row className="content-centered">
            <div>
              <Form noValidate encType='multipart/form-data'>
                <div>
                  <h4><u>Import Data</u></h4>
                  <h6><i>* Only CSV files are supported at this time</i></h6>
                  <Form.Group controlId="data">
                    <Form.Control
                      type="file"
                      placeholder="Choose a file"
                      accept=".csv"
                      onChange={(e) => {
                        console.log(e.target.files);
                        this.setState({ importedFile: e.target.files[0] }, () => {
                          console.log(this.state);
                        });
                      }}/>
                  </Form.Group>
                </div>
                <Button
                  variant='primary'
                  onClick={() => this._handleSubmit(history)}>
                  Import
                </Button>
              </Form>
            </div>
          </Row>
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
