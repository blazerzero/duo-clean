import React from 'react';
import { Router, Switch, Route } from 'react-router-dom';
import logo from './logo.svg';
import Home from './pages/Home';
import Project from './pages/Project';
import history from './history';

import './App.css';

function App() {
  return (
    <Router history={history}>
      <Switch>
        <Route path='/duo/' exact component={Home} />
        <Route path='/duo/project/' component={Project} />
      </Switch>
    </Router>
  );
}

export default App;
