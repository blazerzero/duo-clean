import React, { Component } from 'react';
import {
  Alert,
  Button,
  Col,
  Modal,
  Row,
  Table,
  Spinner,
} from 'react-bootstrap';
import { Route } from 'react-router-dom';
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
          if (msg === '[DONE]') {
            alert('Thank you for participating! Please revisit your instructions to see next steps.');
          }
          else {
            var { sample, contradictions, feedback } = pick(res, ['sample', 'contradictions', 'feedback'])
            var data = JSON.parse(sample);
            contradictions = JSON.parse(contradictions);
            feedback = JSON.parse(feedback);

            for (var i in data) {
              for (var j in data[i]) {
                if (data[i][j] == null) data[i][j] = '';
                else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
              }
            }
            var contradictionMap = await this._buildContradictionMap(data, contradictions);
            var feedbackMap = await this._buildFeedbackMap(data, feedback);
            this.setState({ 
              data,
              contradictionMap,
              feedbackMap,
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
    for (let i = 0; i < rows.length; i++) {
      var tup = {};
      for (let j = 0; j < cols.length; j++) {
        tup[cols[j]] = contradictions.some(e => e.row === parseInt(rows[i]) && e.col === cols[j]);
      }
      contradictionMap[rows[i]] = tup;
    }
    return contradictionMap;
  }

  _buildFeedbackMap = async(data, feedback) => {
    var feedbackMap = {};
    var rows = Object.keys(data);
    var cols = this.state.header;
    for (let i = 0; i < rows.length; i++) {
      var tup = {};
      for (let j = 0; j < cols.length; j++) {
        var cell = feedback.find(e => {
          var trimmedCol = cols[j].replace(/[\n\r]+/g, '');
          return e.row === parseInt(rows[i]) && e.col === trimmedCol;
        });
        tup[cols[j]] = cell.marked;
      }
      feedbackMap[rows[i]] = tup;
    }
    return feedbackMap;
  }

  _getSampleData = async(project_id, sample_size) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    formData.append('sample_size', sample_size);
    console.log(formData.get('project_id'));
    axios.post('http://localhost:5000/duo/api/sample', formData)
        .then(async(response) => {
          var res = JSON.parse(response.data);
          var { sample, contradictions, feedback, msg } = pick(res, ['sample', 'contradictions', 'feedback', 'msg'])
          var data = JSON.parse(sample);
          contradictions = JSON.parse(contradictions);
          feedback = JSON.parse(feedback);
          console.log(data);
          console.log(msg);

          for (var i in data) {
            for (var j in data[i]) {
              if (data[i][j] == null) data[i][j] = '';
              else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
              if (!isNaN(data[i][j]) && Math.ceil(parseFloat(data[i][j])) - parseFloat(data[i][j]) === 0) {
                data[i][j] = Math.ceil(data[i][j]).toString();
              }
            }
          }
          var contradictionMap = await this._buildContradictionMap(data, contradictions);
          var feedbackMap = await this._buildFeedbackMap(data, feedback);
          this.setState({ data, contradictionMap, feedbackMap });
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
    var feedbackMap = this.state.feedbackMap;
    feedbackMap[idx][attr] = !feedbackMap[idx][attr]
    this.setState({ feedbackMap });
  }

  _handleNoNewFeedbackClick = async() => {
    var isNewFeedback = !this.state.isNewFeedback;
    this.setState({ isNewFeedback });
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
      feedbackMap: {},
      contradictionMap: [],
      header: [],
      project_id: 0,
      isProcessing: false,
      isNewFeedback: false,
    };
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
              <p><strong>Scenario #: </strong>{this.state.scenario_number}</p>
              <p><strong>Project ID: </strong>{this.state.project_id}</p>
            </div>
          </Row>
          <Row className='content-centered'>
            <Col md={6}>
              <Alert variant='warning' style={{border: '1px black solid'}}>Yellow cells indicate cells in which <br/>contradicting values occurred while the system<br/>was repairing the dataset.</Alert>
            </Col>
          </Row>
          {Object.keys(this.state.data).length > 0 && (
            <div>
              <div>
                <Table bordered responsive>
                  <thead>
                    <tr>
                      { this.state.header.map((item) => {
                        return <th key={'header_'.concat(item)}>{item}</th>
                      }) }
                    </tr>
                  </thead>
                  <tbody>
                  { Object.keys(this.state.data).map((i) => {
                    return (
                      <tr key={i}>
                        { Object.keys(this.state.data[i]).map((j) => {
                          var key = i.toString().concat('_', j);
                          return <td
                              key={key}
                              style={{cursor: 'pointer', backgroundColor: (!!this.state.contradictionMap[i][j] ? '#FFF3CD' : (this.state.feedbackMap[i][j] ? '#D4EDDA' : 'white'))}}
                              onClick={this._handleCellClick.bind(this, key)}>
                              {this.state.data[i][j]}
                          </td>
                        }) }
                      </tr>
                    )
                  }) }
                  </tbody>
                </Table>
              </div>
              <Row className='content-centered'>
                <Col md={4}>
                  <label>
                    <input
                      type='checkbox'
                      defaultChecked={this.state.isNewFeedback}
                      onChange={this._handleNoNewFeedbackClick}
                      />
                  </label>
                </Col>
                <Col md={{ span: 4, offset: 4 }}>
                  <Button
                      variant='primary'
                      className='btn-round right box-blur'
                      size='lg'
                      onClick={this._handleSubmit}>
                    SUBMIT
                  </Button>
                </Col>
              </Row>
            </div>
          )}
        </div>
      )} />
    );
  }
}

export default Clean;
