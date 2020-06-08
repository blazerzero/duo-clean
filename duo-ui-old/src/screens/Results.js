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
    data: [],
    contradictionMap: [],
    repairMap: [],
    header: [],
    project_id: 0,
    isModalOpen: false,
    modalCellValue: null,
    modalCellKey: null,
  };

  async _handleSubmit() {
    const formData = new FormData();
    formData.append('project_id', this.state.project_id);
    formData.append('data', JSON.stringify(this.state.data));
    formData.append('sample_size', 10);
    axios.post('http://localhost:5000/duo/api/clean', formData)
        .then(async(response) => {
          var { sample, contradictions, changes, msg } = JSON.parse(response.data);
          var data = JSON.parse(sample);
          contradictions = JSON.parse(contradictions);
          changes = JSON.parse(changes);
          for (var i in data) {
            for (var j in data[i]) {
              if (data[i][j] == null) data[i][j] = '';
              else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
            }
          }
          var contradictionMap = await this._buildContradictionMap(data, contradictions);
          var repairMap = await this._buildRepairMap(data, changes);
          this.setState({ data, contradictionMap, repairMap });
        })
        .catch(error => {
          console.log(error);
        });
  }

  async _buildContradictionMap(data, contradictions) {
    var contradictionMap = {};
    var rows = Object.keys(data);
    var cols = this.state.header;
    for (var i = 0; i < rows.length; i++) {
      var tup = {};
      for (var j = 0; j < cols.length; j++) {
        tup[cols[j]] = contradictions.some(e => e.row === parseInt(rows[i]) && e.col === cols[j]);
      }
      contradictionMap[rows[i]] = tup;
    }
    return contradictionMap;
  }

  async _buildRepairMap(data, changes) {
    var repairMap = {};
    var rows = Object.keys(data);
    var cols = this.state.header;
    for (var i = 0; i < rows.length; i++) {
      var tup = {};
      for (var j = 0; j < cols.length; j++) {
        var cell = changes.find(e => e.row === parseInt(rows[i]) && e.col === cols[j]);
        tup[cols[j]] = cell.repaired;
      }
      repairMap[rows[i]] = tup;
    }
    return repairMap;
  }

  async _getSampleData(project_id, sample_size) {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/duo/api/sample', formData)
        .then(async(response) => {
          var { sample, contradictions, changes, msg } = JSON.parse(response.data);
          var data = JSON.parse(sample);
          contradictions = JSON.parse(contradictions);
          changes = JSON.parse(changes);
          console.log(data);
          console.log(msg);
          for (var i in data) {
            for (var j in data[i]) {
              if (data[i][j] == null) data[i][j] = '';
              else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
            }
          }
          var contradictionMap = await this._buildContradictionMap(data, contradictions);
          var repairMap = await this._buildRepairMap(data, changes);
          this.setState({ data, contradictionMap, repairMap });
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
      modalCellValue: this.state.data[idx][attr],
      modalCellKey: key,
      isModalOpen: true
    });
  }

  async _handleDone(key, event) {
    alert('Thank you for participating! Please revisit your instructions to see next steps.');
  }

  async _closeModal() {
    this.setState({ isModalOpen: false });
  }

  async _saveChange() {
    var newCellValue = this.newCellValue.current.value;
    var data = this.state.data;
    var keyPieces = this.state.modalCellKey.split('_');
    var idx = parseInt(keyPieces.shift());
    var attr = keyPieces.join('_');
    data[idx][attr] = newCellValue;

    for (var i in data) {
      for (var j in data[i]) {
        if (data[i][j] == null) data[i][j] = '';
        else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
      }
    }

    this.setState({
      data,
      modalCellValue: null,
      modalCellKey: null,
      isModalOpen: false,
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
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page'>
          <Modal show={this.state.isModalOpen} onHide={this._closeModal} animation={false}>
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
            <Col>
              <Alert variant='success' style={{border: '1px black solid'}}>Green cells indicate cells that<br/>the system repaired.</Alert>
            </Col>
            <Col>
              <Alert variant='warning' style={{border: '1px black solid'}}>Yellow cells indicate cells in which <br/>contradicting values occurred while the system<br/>was repairing the dataset.</Alert>
            </Col>
          </Row>
          <div>
            <Table bordered responsive>
              <thead>
                <tr>{ this.state.header.map((item) => {
                  return <th key={'header_'.concat(item)}>{item}</th>
                }) }</tr>
              </thead>
              <tbody>
              { Object.keys(this.state.data).map((i) => {
                return (
                    <tr key={i}>
                      { Object.keys(this.state.data[i]).map((j) => {
                        var key = i.toString().concat('_', j);
                        return <td
                            key={key}
                            style={{cursor: 'pointer', backgroundColor: (this.state.contradictionMap[i][j] ? '#FFF3CD' : (this.state.repairMap[i][j] ? '#D4EDDA' : 'white'))}}
                            onClick={this._handleCellClick.bind(this, key)}>{this.state.data[i][j]}
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
                onClick={this._handleDone}>
              DONE
            </Button>
            {/*<Button
                variant='success'
                className='btn-round right box-blur'
                size='lg'
                onClick={this._handleDownload}>
              DOWNLOAD
            </Button>*/}
          </div>
        </div>
      )} />
    );
  }
}

export default Results;
