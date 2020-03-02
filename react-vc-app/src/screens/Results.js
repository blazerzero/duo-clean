import React, { Component } from 'react';
import {
  Alert,
  Button,
  Col,
  Dropdown,
  Form,
  Modal,
  Row,
  Table,
} from 'react-bootstrap';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import axios from 'axios';
//import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';

import '../css/App.css';
//import '../../../node_modules/react-bootstrap-table/dist/react-bootstrap-table-all-min.css';
import undo from '../images/corner-up-left.svg';
import redo from '../images/corner-up-right.svg';

class Results extends Component {

  state = {
    dirtyData: [],
    cleanData: [],
    typeMap: [],
    contradictionMap: [],
    header: [],
    project_id: 0,
    modal: false,
    modalCellValue: null,
    modalCellKey: null,
  };

  async _handleSubmit() {
    const formData = new FormData();
    formData.append('project_id', this.state.project_id);
    formData.append('data', JSON.stringify(this.state.cleanData));
    formData.append('sample_size', 10);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/clean', formData)
        .then(async(response) => {
          var { sample, contradictions, msg } = JSON.parse(response.data);
          var data = JSON.parse(sample);
          contradictions = JSON.parse(contradictions);
          console.log(data);
          console.log(msg);
          for (var i in data) {
            for (var j in data[i]) {
              if (data[i][j] == null) data[i][j] = '';
              else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
            }
          }
          //var modMap = await this._buildModMap(data, data);
          var contradictionMap = await this._buildContradictionMap(data, contradictions);
          this.setState({ dirtyData: data, cleanData: data, contradictionMap }, () => {
            //var typeMap = this._buildTypeMap(this.state.cleanData);
            //this.setState({ typeMap });
          });
        })
        .catch(error => {
          console.log(error);
        });
  }

  async _handleDownload() {
    const formData = new FormData();
    formData.append('project_id', this.state.project_id);
    axios.post('http://localhost:5000/download', formData, {
      responseType: 'arraybuffer',
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    })
        .then((response) => {
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', 'charm_cleaned.zip');
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        })
        .catch(error => {
          console.log(error);
        })
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
        tup[cols[j]] = typeof(data[rows[i]][cols[j]])
      }
      typeMap[rows[i]] = tup;
    }
    console.log(typeMap);
    return typeMap;
  }

  async _buildContradictionMap(data, contradictions) {
    console.log(contradictions);
    var contradictionMap = {};
    var rows = Object.keys(data);
    var cols = this.state.header;
    for (var i in rows) {
      var tup = {};
      for (var j in cols) {
        //console.log(contradictions.length);
        tup[cols[j]] = contradictions.some(e => e.row == i && e.col == j)
      }
      contradictionMap[rows[i]] = tup;
    }
    return contradictionMap;
  }

  async _buildModMap(dirtyData, cleanData) {
    var modMap = {};
    var rows = Object.keys(cleanData);
    var cols = this.state.header;
    for (var i in rows) {
      var tup = {};
      for (var j in cols) {
        //console.log(dirtyData[rows[i]][cols[j]]);
        //console.log(cleanData[rows[i]][cols[j]]);
        tup[cols[j]] = (dirtyData[rows[i]][cols[j]] === cleanData[rows[i]][cols[j]]);
      }
      modMap[rows[i]] = tup;
    }
    console.log(modMap);
    return modMap;
  }

  async _getSampleData(project_id, sample_size) {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/sample', formData)
        .then(async(response) => {
          var { sample, contradictions, msg } = JSON.parse(response.data);
          var data = JSON.parse(sample);
          contradictions = JSON.parse(contradictions);
          console.log(data);
          console.log(msg);
          for (var i in data) {
            for (var j in data[i]) {
              if (data[i][j] == null) data[i][j] = '';
              else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
            }
          }
          //var modMap = await this._buildModMap(data, data);
          /*for (var i in modMap) {
            for (var j in modMap[i]) {
              j = j.trim();
            }
          }
          for (var i in contradictionMap) {
            for (var j in contradictionMap[i]) {
              j = j.trim();
            }
          }*/
          //console.log(modMap);
          var contradictionMap = await this._buildContradictionMap(data, contradictions);
          this.setState({ dirtyData: data, cleanData: data, contradictionMap }, () => {
            //var typeMap = this._buildTypeMap(this.state.cleanData);
            //this.setState({ typeMap });
          });
        })
        .catch(error => {
          console.log(error);
        });
  }

  async _renderHeader() {
    console.log('building header');
    return this.state.header.map((item, idx) => <th key={'header_'.concat(idx)}>{item}</th>);
  }


  async _handleCellClick(key, event) {
    var pieces = key.split('_');
    var idx = parseInt(pieces.shift());
    var attr = pieces.join('_');
    this.setState({
      modalCellValue: this.state.cleanData[idx][attr],
      modalCellKey: key,
      modal: true
    });
  }

  async _closeModal() {
    this.setState({ modal: false });
  }

  async _saveChange() {
    var newCellValue = this.newCellValue.current.value;
    var cleanData = this.state.cleanData;
    var keyPieces = this.state.modalCellKey.split('_');
    var idx = parseInt(keyPieces.shift());
    var attr = keyPieces.join('_');
    cleanData[idx][attr] = newCellValue;

    for (var i in cleanData) {
      for (var j in cleanData[i]) {
        if (cleanData[i][j] == null) cleanData[i][j] = '';
        else if (typeof cleanData[i][j] != 'string') cleanData[i][j] = cleanData[i][j].toString();
      }
    }

    //var modMap = await this._buildModMap(this.state.dirtyData, cleanData);

    this.setState({
      cleanData,
      modalCellValue: null,
      modalCellKey: null,
      modal: false,
      //modMap,
    });
  }

  componentDidMount() {
    const { header, project_id } = this.props.location;
    this.setState({ header, project_id }, async() => {
      await this._getSampleData(this.state.project_id, 10);
      console.log('got sample');
      console.log(this.state);
    });
  }

  constructor(props) {
    super(props);
    this.newCellValue = React.createRef();
    this._closeModal = this._closeModal.bind(this);
    this._saveChange = this._saveChange.bind(this);
    this._handleSubmit = this._handleSubmit.bind(this);
    this._handleDownload = this._handleDownload.bind(this);
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page'>
          <Modal show={this.state.modal} onHide={this._closeModal} animation={false}>
            <Form onSubmit={this._saveChange}>
              <Modal.Header closeButton>
                <Modal.Title>Edit Cell</Modal.Title>
              </Modal.Header>
              <Modal.Body>
                <Form.Group>
                  <Form.Label><strong>Current Value: </strong>{this.state.modalCellValue}</Form.Label>
                </Form.Group>
                <Form.Group>
                  <Form.Label><strong>New Value</strong></Form.Label>
                  <Form.Control ref={this.newCellValue} defaultValue={this.state.modalCellValue}></Form.Control>
                </Form.Group>
              </Modal.Body>
              <Modal.Footer>
                <Button variant='secondary' onClick={this._closeModal}>
                  Cancel
                </Button>
                <Button variant='primary' type='submit'>
                  Save
                </Button>
              </Modal.Footer>
            </Form>
          </Modal>
          <Row className='content-centered'>
            <div className='results-header box-blur'>
              <span className='results-title'>DuoClean</span>
              <p><strong>Project ID: </strong>{this.state.project_id}</p>
            </div>
          </Row>
          <Row className='content-centered'>
            <Alert variant='warning' style={{border: '1px black solid'}}>Yellow cells indicate cells in which a<br/>contradiction occurred while the system<br/>was cleaning the dataset.</Alert>
          </Row>
          <div>
            <Table bordered responsive>
              <thead>
                <tr>{ this.state.header.map((item) => {
                  return <th key={'header_'.concat(item)}>{item}</th>
                }) }</tr>
              </thead>
              <tbody>
              { Object.keys(this.state.cleanData).map((i) => {
                return (
                    <tr key={i}>
                      { Object.keys(this.state.cleanData[i]).map((j) => {
                        var key = i.toString().concat('_', j);
                        return <td
                            key={key}
                            style={{cursor: 'pointer', backgroundColor: (this.state.contradictionMap[i][j] && 'yellow')}}
                            onClick={this._handleCellClick.bind(this, key)}>{this.state.cleanData[i][j]}
                        </td>
                      }) }
                    </tr>
                )
              }) }
              </tbody>
            </Table>
          </div>
          <div className='content-centered'>
            <Button
                variant='primary'
                className='btn-round right box-blur'
                size='lg'
                onClick={this._handleSubmit}>
              SUBMIT CHANGES AND SEE NEW EXAMPLES
            </Button>
            <Button
                variant='success'
                className='btn-round right box-blur'
                size='lg'
                onClick={this._handleDownload}>
              DOWNLOAD
            </Button>
          </div>
        </div>
      )} />
    );
  }
}

export default Results;
