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
    data: [],
    selected: [],
  }

  async _handleSubmitAndRegenerate() {

  }

  async _handleSubmitAndClean() {

  }

  async _handleRefresh() {

  }

  componentDidMount() {
    const { data } = this.props.location;
    this.setState({ data });
  }

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <Route render={({ history }) => (
        <div className='site-page'>

        </div>
      )} />
    );
  }
}

export default Results;
