import React, { Component } from 'react';
import {
  Button,
  Col,
  Form,
  Row,
  Table,
} from 'react-bootstrap';
import '../css/App.css';

class Results extends Component {
  _handleShowRestartModal() {

  }

  render() {
    return (
      <div>
        <div className='body-section'>
          <div className='top-level'>
            <Button className='restart-btn' variant='danger' onClick={() => this._handleShowRestartModal}>Restart</Button>
            <Button className='export-btn' variant='primary'>Export to CSV</Button>
          </div>
          <div className='middle-action-btn-section'>
            <Button className='btn-undo' variant='light' disabled>
              Undo
            </Button>
            <Button className='btn-redo' variant='light' disabled>
              Redo
            </Button>
          </div>
        </div>
        <Row className='body-section'>
          <Col className='body-col'>
            <div className="key-box">
              <h5><strong><u>Key</u></strong></h5>
              <div>Unmarked cells are clean</div>
              <div>Dirty cells:</div>
              <div className="dirty-color-line"></div>
              <div className="dirty-color-line-labels">
                <div className="less"><small>Less valuable to fix</small></div>
                <div className="more"><small>More valuable to fix</small></div>
              </div>
            </div>
            <div className="repairs-applied-box">
              <h5><strong><u>Repairs Applied</u></strong></h5>
              <div id="currentRepairList">No repairs applied yet</div>
            </div>
          </Col>
          <Col className="result-content">
            <Table bordered>
              <thead>
                <tr>
                  <th>Placeholder</th>
                  <th>Placeholder</th>
                </tr>
              </thead>
              <tbody>
              </tbody>
            </Table>
          </Col>
        </Row>
      </div>
    );
  }
}

export default Results;
