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
    dirtyData: [],
    cleanData: [],
    header: null,
    project_id: 0,
  }

  async _handleSubmit() {

  }

  async _handleRefresh() {

  }

  async _processSample(response) {
    console.log(response.msg);
    var dirtyData = JSON.parse(response.sample);
    var cleanData = JSON.parse(response.sample);
    this.setState({ dirtyData, cleanData });
  }

  async _getSample(project_id, sample_size) {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/sample', formData)
      .then((response) => {
        console.log(response.msg);
        var res = JSON.parse(response.data);
        var dirtyData = JSON.parse(res.sample);
        var cleanData = JSON.parse(res.sample);
        console.log(cleanData);
        this.setState({ dirtyData, cleanData }, () => { console.log(this.state.cleanData) });
      })
      .catch(error => console.log(error));
  }

  async _renderSample() {
    console.log(this.state.cleanData);
    var sample = [];
    //console.log(Object.keys(this.state.cleanData));
    //console.log(Object.keys(this.state.cleanData[0]));
    Object.keys(this.state.cleanData).forEach((key) => {
      sample.push({key, value: this.state.cleanData[key]});
    });
    for (var i = 0; i < sample.length; i++) {
      var temp = [];
      Object.keys(sample[i]).forEach((key) => {
        temp.push({key, value: sample[i][key]});
      });
      sample[i].value = temp;
    }
    console.log(sample);
    console.log(sample[0])
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
              {row.map(item => <td key={item.key}>{item.value}</td>)}
            </tr>
          ))}
        </tbody>
      </Table>
    )
  }

  async _isPromise(obj) {
    return obj instanceof Promise;
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
            { Object.keys(this.state.cleanData).length > 0 && this._isPromise(this.state.cleanData) !== true && this._getSample() }
          </div>
        </div>
      )} />
    );
  }
}

export default Results;
