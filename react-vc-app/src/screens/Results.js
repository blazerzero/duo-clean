import React, { Component } from 'react';
import {
  Button,
  Col,
  Form,
  Row,
  Table,
} from 'react-bootstrap';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import { connect } from 'react-redux';
import axios from 'axios';

import '../css/App.css';
import undo from '../images/corner-up-left.svg';
import redo from '../images/corner-up-right.svg';

class Results extends Component {

  state = {
    dirtyData: null,
    cleanData: null,
    header: null,
    project_id: 0,
  }

  async _handleSubmit() {

  }

  async _handleRefresh() {

  }

  async _getSample(project_id) {
    const formData = new FormData();
    formData.append('project_id', project_id);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/sample', formData)
      .then(response => {
        console.log(response);
        console.log(JSON.parse(response.sample));
        var dirtyData = JSON.parse(response.sample);
        var cleanData = JSON.parse(response.sample);
      })
      .catch(error => console.log(error));
  }

  async _renderSample() {
    var sample = [];
    Object.keys(this.state.cleanData).forEach((key) => {
      sample.push(this.state.cleanData[key]);
    });
    return (
      <Table bordered responsive>
        <thead>
          <tr>
            {this.state.header.map(item => <th>{item}</th>)}
          </tr>
        </thead>
        <tbody>
          {this.state.cleanData.map(row => (
            <tr>
              {row.map(item => <td key={item.id}>{item.value}</td>)}
            </tr>
          ))}
        </tbody>
      </Table>
    )
  }

  componentDidMount() {
    const { dataURL } = this.props.location;
    this.setState({ dataURL }, () => {
      var dirtyData = this._getSample(this.state.project_id);
    });
  }

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page'>
          <Row className='content-centered'>
            <div className='results-header box-blur'>
              <span className='results-title'>CharmClean</span>
            </div>
          </Row>
          <div>
            { this.state.cleanData != null && this._renderSample() }
          </div>
        </div>
      )} />
    );
  }
}

export default Results;
