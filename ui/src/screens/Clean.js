import React, { Component } from 'react';
import {
  Alert,
  Button,
  Col,
  Form,
  Modal,
  Row,
  Table,
  Spinner,
} from 'react-bootstrap';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import axios from 'axios';
import { pick } from 'lodash';

class Clean extends Component {

  _handleSubmit = async() => {
    this.setState({ isProcessing: true });
    const formData = new FormData();
    formData.append('project_id', this.state.project_id);
    formData.append('data', JSON.stringify(this.state.data));
    formData.append('noisy_tuples', JSON.stringify(this.state.noisyTuples));
    formData.append('sample_size', 10);
    axios.post('http://localhost:5000/duo/api/clean', formData)
        .then(async(response) => {
          console.log(response.data);
          var res = JSON.parse(response.data);
          var { msg } = pick(res, ['msg'])
          if (msg == '[DONE]') {
            alert('Thank you for participating! Please revisit your instructions to see next steps.');
          }
          else {
            var { sample, contradictions, changes } = pick(res, ['sample', 'contradictions', 'changes'])
            var data = JSON.parse(sample);
            contradictions = JSON.parse(contradictions);
            changes = JSON.parse(changes);

            var noisyTuples = {};
            for (var i in data) {
              noisyTuples[i] = false;
              for (var j in data[i]) {
                if (data[i][j] == null) data[i][j] = '';
                else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
              }
            }
            var contradictionMap = await this._buildContradictionMap(data, contradictions);
            var changeMap = await this._buildChangeMap(data, changes);
            this.setState({ 
              data,
              noisyTuples,
              contradictionMap,
              changeMap,
              isProcessing: false
            });
          }
        })
        .catch(error => {
          console.log(error);
        });
  }

  _buildContradictionMap = async(data, contradictions) => {
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

  _buildChangeMap = async(data, changes) => {
    var changeMap = {};
    var rows = Object.keys(data);
    var cols = this.state.header;
    for (var i = 0; i < rows.length; i++) {
      var tup = {};
      for (var j = 0; j < cols.length; j++) {
        var cell = changes.find(e => {
          var trimmedCol = cols[j].replace(/[\n\r]+/g, '');
          return e.row === parseInt(rows[i]) && e.col === trimmedCol;
        });
        tup[cols[j]] = cell.changed;
      }
      changeMap[rows[i]] = tup;
    }
    return changeMap;
  }

  _getSampleData = async(project_id, sample_size) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/duo/api/sample', formData)
        .then(async(response) => {
          var res = JSON.parse(response.data);
          var { sample, contradictions, changes, msg } = pick(res, ['sample', 'contradictions', 'changes', 'msg'])
          var data = JSON.parse(sample);
          contradictions = JSON.parse(contradictions);
          changes = JSON.parse(changes);
          console.log(data);
          console.log(msg);

          var noisyTuples = {};
          for (var i in data) {
            noisyTuples[i] = false;
            for (var j in data[i]) {
              if (data[i][j] == null) data[i][j] = '';
              else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
              if (!isNaN(data[i][j]) && Math.ceil(parseFloat(data[i][j])) - parseFloat(data[i][j]) === 0) {
                data[i][j] = Math.ceil(data[i][j]).toString();
              }
            }
          }
          var contradictionMap = await this._buildContradictionMap(data, contradictions);
          var changeMap = await this._buildChangeMap(data, changes);
          this.setState({ data, contradictionMap, changeMap });
        })
        .catch(error => {
          console.log(error);
        });
  }

  _renderHeader = async() => {
    console.log('building header');
    return this.state.header.map((item, idx) => <th key={'header_'.concat(idx)}>{item}</th>);
  }


  _handleCellClick = async(key, event) => {
    var pieces = key.split('_');
    var idx = parseInt(pieces.shift());
    var attr = pieces.join('_');
    this.setState({
      modalCellValue: this.state.data[idx][attr],
      modalCellKey: key,
      isModalOpen: true
    });
  }

  _handleNoisyCheckboxClick = (event) => {
    var idx = parseInt(event.target.value);
    var noisyTuples = this.state.noisyTuples;
    noisyTuples[idx] = !noisyTuples[idx];
    console.log(noisyTuples);
    this.setState({ noisyTuples });
  }

  _closeModal = async() => {
    this.setState({ isModalOpen: false });
  }

  _saveChange = async() => {
    var newCellValue = this.newCellValue.current.value;
    var data = this.state.data;
    var keyPieces = this.state.modalCellKey.split('_');
    var idx = parseInt(keyPieces.shift());
    var attr = keyPieces.join('_');
    data[idx][attr] = newCellValue;

    for (var i in data) {
      for (var j in data[i]) {
        if (typeof data[i][j] == 'number') data[i][j] = Math.trunc(data[i][j]);
        if (data[i][j] == null) data[i][j] = '';
        else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
      }
    }

    var noisyTuples = this.state.noisyTuples;
    noisyTuples[idx] = true;
    console.log(noisyTuples);

    this.setState({
      data,
      noisyTuples,
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

    this.state = {
      data: [],
      noisyTuples: {},
      contradictionMap: [],
      changeMap: [],
      header: [],
      project_id: 0,
      isModalOpen: false,
      modalCellValue: null,
      modalCellKey: null,
      isProcessing: false,
    };

    this.newCellValue = React.createRef();
    this._closeModal = this._closeModal.bind(this);
    this._saveChange = this._saveChange.bind(this);
    this._handleSubmit = this._handleSubmit.bind(this);
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page'>
          <Modal show={this.state.isProcessing} animation={false} backdrop='static'>
            <Modal.Body>
              <p><strong>Processing...</strong></p>
              <Spinner animation='border' />
            </Modal.Body>
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
          {Object.keys(this.state.data).length > 0 && (
            <div>
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
              <div>
                <Table bordered responsive>
                  <thead>
                    <tr>
                      <th>Noisy Tuple?</th>
                      { this.state.header.map((item) => {
                        return <th key={'header_'.concat(item)}>{item}</th>
                      }) }
                    </tr>
                  </thead>
                  <tbody>
                  { Object.keys(this.state.data).map((i) => {
                    return (
                        <tr key={i}>
                          <td name={i.toString().concat('_noisy')}>
                            <input
                              type='checkbox'
                              value={i}
                              checked={!!this.state.noisyTuples[i]}
                              onChange={this._handleNoisyCheckboxClick.bind(this)}
                              />
                          </td>
                          { Object.keys(this.state.data[i]).map((j) => {
                            var key = i.toString().concat('_', j);
                            return <td
                                key={key}
                                style={{cursor: 'pointer', backgroundColor: (!!this.state.contradictionMap[i][j] ? '#FFF3CD' : (this.state.changeMap[i][j] ? '#D4EDDA' : 'white'))}}
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
                {/* <Button
                    variant='success'
                    className='btn-round right box-blur'
                    size='lg'
                    onClick={this._handleDone}>
                  DONE
                </Button>
                <Button
                    variant='success'
                    className='btn-round right box-blur'
                    size='lg'
                    onClick={this._handleDownload}>
                  DOWNLOAD
                </Button> */}
              </div>
            </div>
          )}
        </div>
      )} />
    );
  }
}

export default Clean;
