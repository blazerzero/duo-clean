import React, { Component } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import {
  Button,
  Col,
  Form,
  Row,
} from 'react-bootstrap';
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
    uploadedFile: null,
  }

  _handleSubmit(e) {
    if (this.state.uploadedFile != null) {
      this.props.history.push('/results/');
    }
  };

  render() {
    return (
      <div className="body-section">
        <Row className="content-centered">
          <div>
            <Form noValidate encType='multipart/form-data' onSubmit={() => this._handleSubmit}>
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
                      this.setState({ uploadedFile: e.target.files[0] }, () => {
                        console.log(this.state);
                      });
                    }}/>
                </Form.Group>
              </div>
              <ImportButton />
            </Form>
          </div>
        </Row>
      </div>
    );
  }
}

export default Import;
