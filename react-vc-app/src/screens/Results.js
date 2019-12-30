import React, { Component } from 'react';
import {
  Button,
  Col,
  Form,
  Row,
  Table,
} from 'react-bootstrap';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import axios from 'axios';

import '../css/App.css';
import undo from '../images/corner-up-left.svg';
import redo from '../images/corner-up-right.svg';

class Results extends Component {

  state = {
    dirtyData: [],
    cleanData: [],
    typeMap: [],
    header: [],
    project_id: 0,
  };

  async _handleSubmit() {

  }

  async _handleRefresh() {

  }

  async _buildTypeMap(data) {
    var typeMap = {};
    var rows = Object.keys(data);
    var cols = this.state.header;
    for (var i in rows) {
      var tup = {};
      for (var j in cols) {
        tup[rows[j]] = typeof(data[rows[i]][cols[j]])
      }
      typeMap[i] = tup;
    }
    console.log(typeMap);
    return typeMap;
  }

  async _getSampleData(project_id, sample_size) {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/sample', formData)
      .then(async(response) => {
        var { sample, msg } = JSON.parse(response.data);
        var data = JSON.parse(sample);
        console.log(data);
        console.log(msg);
        this.setState({ dirtyData: data, cleanData: data }, () => {
          var typeMap = this._buildTypeMap(this.state.cleanData);
          this.setState({ typeMap });
        });
      })
      .catch(error => {
        console.log(error);
        return null;
      });
  }

  async _renderHeader() {
    console.log('building header');
    return this.state.header.map((item, idx) => <th key={'header_'.concat(idx)}>{item}</th>);
  }

  componentDidMount() {
    const { header, project_id } = this.props.location;
    this.setState({ header, project_id }, async() => {
      await this._getSampleData(this.state.project_id, 10);
      console.log('got sample');
      console.log(this.state);
    });
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
            <Table bordered responsive>
              <thead>
                <tr>{ this.state.header.map((item) => {
                  return <th key={'header_'.concat(item)}>{item}</th>
                }) }</tr>
              </thead>
              <tbody>
              { Object.keys(this.state.cleanData).map((idx) => {
                return (
                    <tr key={idx}>
                      { Object.keys(this.state.cleanData[idx]).map((key) => {
                        return <td key={idx.toString().concat('_', key)}>{this.state.cleanData[idx][key]}</td>
                      }) }
                    </tr>
                )
              }) }
              </tbody>
            </Table>
          </div>
        </div>
      )} />
    );
  }
}

export default Results;
