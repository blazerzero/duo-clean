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

  async _getSample(project_id, sample_size) {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    var self = this;
    axios.post('http://localhost:5000/sample', formData)
      .then((response) => {
        console.log(response.data);
        var res = JSON.parse(response.data);
        var dirtyData = res.sample;
        var cleanData = res.sample;
        self.setState({ dirtyData, cleanData });
      })
      .catch(error => console.log(error));
  }

  async _renderSample() {
    console.log(this.state.cleanData);
    var sample = [];
    //console.log(Object.keys(this.state.cleanData));
    //console.log(Object.keys(this.state.cleanData[0]));
    /*Object.keys(this.state.cleanData).forEach((key) => {
      sample.push(this.state.cleanData[key]);
    });*/
    for (var i in this.state.cleanData) {
      sample.push([i, this.state.cleanData[i]]);
    }
    console.log(sample);
    return (
      <Table bordered responsive>
        <thead>
          <tr>
            {this.state.header.map(item => <th>{item}</th>)}
          </tr>
        </thead>
        <tbody>
          {sample.map(row => (
            <tr>
              {row.map(item => <td key={item.id}>{item.value}</td>)}
            </tr>
          ))}
        </tbody>
      </Table>
    )
  }

  componentDidMount() {
    const { header, project_id } = this.props.location;
    this.setState({ header, project_id }, () => {
      this._getSample(this.state.project_id, 10);
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
