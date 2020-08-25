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
    formData.append('feedback', JSON.stringify(this.state.feedbackMap));
    formData.append('is_new_feedback', (this.state.noNewFeedback === false ? 1 : 0));
    axios.post('http://167.71.155.153:5000/duo/api/clean', formData)
        .then(async(response) => {
          console.log(response.data);
          var res = JSON.parse(response.data);
          var { msg } = pick(res, ['msg'])
          if (msg === '[DONE]') {
            this.setState({ interactionDone: true});
          }
          else {
            var { sample, feedback, leaderboard } = pick(res, ['sample', 'feedback', 'leaderboard'])
            var data = JSON.parse(sample);
            leaderboard = JSON.parse(leaderboard);
            feedback = JSON.parse(feedback);
            console.log(msg);

            for (var i in data) {
              for (var j in data[i]) {
                if (data[i][j] == null) data[i][j] = '';
                else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
              }
            }
            console.log(data);

            var feedbackMap = await this._buildFeedbackMap(data, feedback);
            this.setState({ 
              data,
              feedbackMap,
              isProcessing: false,
              noNewFeedback: false,
              leaderboard
            }, () => {
              console.log(this.state.leaderboard);
            });
          }
        })
        .catch(error => {
          console.log(error);
        });
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

  _getSampleData = async(project_id) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    console.log(formData.get('project_id'));
    axios.post('http://167.71.155.153:5000/duo/api/sample', formData)
        .then(async(response) => {
          var res = JSON.parse(response.data);
          var { sample, feedback, msg, leaderboard } = pick(res, ['sample', 'feedback', 'msg', 'leaderboard'])
          var data = JSON.parse(sample);
          leaderboard = JSON.parse(leaderboard);
          feedback = JSON.parse(feedback);
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
          console.log(data);

          var feedbackMap = await this._buildFeedbackMap(data, feedback);
          this.setState({ data, feedbackMap, leaderboard }, () => {
            console.log(this.state.leaderboard);
          });
        })
        .catch(error => {
          console.log(error);
        });
  }

  _handleResume = async(sample, leaderboard, feedback) => {
    var data = JSON.parse(sample);
    leaderboard = JSON.parse(leaderboard);
    feedback = JSON.parse(feedback);

    for (var i in data) {
      for (var j in data[i]) {
        if (data[i][j] == null) data[i][j] = '';
        else if (typeof data[i][j] != 'string') data[i][j] = data[i][j].toString();
        if (!isNaN(data[i][j]) && Math.ceil(parseFloat(data[i][j])) - parseFloat(data[i][j]) === 0) {
          data[i][j] = Math.ceil(data[i][j]).toString();
        }
      }
    }
    console.log(data);

    var feedbackMap = await this._buildFeedbackMap(data, feedback);
    this.setState({ data, feedbackMap, leaderboard }, () => {
      console.log(this.state.leaderboard);
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

  _handleRefreshClick = async() => {
    var noNewFeedback = true;
    this.setState({ noNewFeedback }, async () => {
      await this._handleSubmit();
    });
  }

  _handleDone = async() => {
    this.setState({ isProcessing: true, interactionDone: true });
  }

  componentDidMount() {
    const { header, project_id, scenario_id, scenario_desc, is_resuming, sample, leaderboard, feedback } = this.props.location;
    this.setState({ header, project_id, scenario_id, scenario_desc }, async() => {
      if (is_resuming === false) {
        await this._getSampleData(this.state.project_id);
        console.log('got sample');
      } else {
        await this._handleResume(sample, leaderboard, feedback);
        console.log('resumed');
      }
      console.log(this.state);
    });
  }

  constructor(props) {
    super(props);

    this.state = {
      data: [],
      feedbackMap: {},
      header: [],
      project_id: 0,
      scenario_id: 0,
      isProcessing: false,
      noNewFeedback: false,
      leaderboard: {},
      interactionDone: false,
      scenario_desc: null,
    };
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page'>
          <Modal show={this.state.isProcessing} animation={false} backdrop='static'>
            <Modal.Body>{
              this.state.interactionDone && (
                <Col md={4} className='content-centered'>
                  <h4>Thank you for participating! Please see your handout for next steps!</h4>
                  <div className='results-header box-blur'>
                    <p><strong>Leaderboard</strong></p>
                    <hr />
                    <Table responsive>
                      <thead>
                        <tr>
                          <th><p><strong>Rank</strong></p></th>
                          <th><p><strong>Name</strong></p></th>
                          <th><p><strong>Score</strong></p></th>
                        </tr>
                      </thead>
                      <tbody>
                        { this.state.leaderboard.map((ranking, idx) => {
                          var key = 'leader'.concat(idx);
                          return (
                            <tr key={key}>
                              <td key={key.concat('_rank')}>{ranking.rank}</td>
                              <td key={key.concat('_name')}>{ranking.name}</td>
                              <td key={key.concat('_score')}>{ranking.score}</td>
                            </tr>
                          )
                        }) }
                      </tbody>
                    </Table>
                  </div>
                </Col>
              )}
              { this.state.interactionDone === false && (
                <div>
                  <p><strong>'Processing...'</strong></p>
                  <Spinner animation='border' />  
                </div>
              )}
            </Modal.Body>
          </Modal>
          <Row className='content-centered'>
            <Col md={4}>
              <p style={{float: 'left'}}><a href="https://github.com/blazerzero/duo-help">Need help or a guide? Click here!</a></p>
            </Col>
            <Col>
              <div className='results-header box-blur'>
                <span className='results-title'>Duo</span>
                <p><strong>Scenario Description: </strong>{this.state.scenario_desc}</p>
                <p><strong>Project ID: </strong>{this.state.project_id}</p>
              </div>
            </Col>
          </Row>
          <Row className='content-centered'>
            <Col md={7}>
              <Alert variant='warning' style={{border: '1px black solid'}}>Yellow cells indicate cells you marked as noisy.</Alert>
            </Col>
          </Row>
          {Object.keys(this.state.data).length > 0 && (
            <div>
              <Row className='content-centered'>
                <Col>
                  <Row>
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
                                  style={{cursor: 'pointer', backgroundColor: (!!this.state.feedbackMap[i][j] ? '#FFF3CD' : 'white')}}
                                  onClick={this._handleCellClick.bind(this, key)}>
                                  {this.state.data[i][j]}
                              </td>
                            }) }
                          </tr>
                        )
                      }) }
                      </tbody>
                    </Table>
                  </Row>
                  <Row>
                    <Col md={4}>
                      <Button
                          variant='primary'
                          className='btn-round right box-blur'
                          size='lg'
                          onClick={this._handleRefreshClick}>
                        REFRESH SAMPLE
                      </Button>
                    </Col>
                    <Col md={{ span: 4, offset: 4 }}>
                      <Row>
                        <Button
                            variant='success'
                            className='btn-round right box-blur'
                            size='lg'
                            onClick={this._handleSubmit}>
                          SUBMIT FEEDBACK
                        </Button>
                        <Button
                            variant='secondary'
                            className='btn-round right box-blur'
                            size='lg'
                            onClick={this._handleDone}>
                          I'M ALL DONE
                        </Button>
                      </Row>
                    </Col>
                  </Row>
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
