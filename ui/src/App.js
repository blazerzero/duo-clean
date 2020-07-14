import React, { Component } from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import './css/App.css';

import Import from './screens/Import';
import Clean from './screens/Clean';

class App extends Component {
  render() {
    return (
      <Router>
        <Route path='/duo/' exact component={Import} />
        <Route path='/duo/clean/' component={Clean} />
      </Router>
    );
  }
}

export default App;
