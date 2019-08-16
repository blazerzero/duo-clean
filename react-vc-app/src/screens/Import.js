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

  _handleSubmit(history) {
    if (this.state.importedFile != null) {
      this.props.importFile(this.state)
      history.push('/results/');
    }
  };

  render() {
    return (
      <Route render={({ history }) => (
        <div className="body-section">
          <Row className="content-centered">
            <div>
              <Form noValidate encType='multipart/form-data' onSubmit={() => this._handleSubmit(history)}>
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
                  type='submit'
                  variant='primary'>
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

const mapStateToProps = (state) => {
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

export default connect(mapStateToProps, mapDispatchToProps)(Import);
