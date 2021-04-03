import React, { Component } from 'react';
import { Dropdown } from 'react-bootstrap';
import '../css/App.css';

class Header extends Component {
  render() {
    return (
      <div>
        <h1 className="content-centered title">VarClean</h1>
        <Dropdown.Divider />
      </div>
    );
  }
}

export default Header;
