import React, { Component } from 'react';
import { PersistGate } from 'redux-persist/integration/react';
import { Provider } from 'react-redux';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import { store, persistor } from './store.js';
import './css/App.css';

import Import from './screens/Import';
import Project from './screens/Project';

class App extends Component {
  render() {
    return (
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <Router>
            <Route path='/duo/' exact component={Import} />
            <Route path='/duo/project/' component={Project} />
          </Router>
        </PersistGate>
      </Provider>
    );
  }
}

export default App;
