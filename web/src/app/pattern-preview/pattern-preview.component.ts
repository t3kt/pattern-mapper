import { Component, OnInit } from '@angular/core';
import {environment} from '../../environments/environment';

@Component({
  selector: 'pm-pattern-preview',
  templateUrl: './pattern-preview.component.html',
  styleUrls: ['./pattern-preview.component.css']
})
export class PatternPreviewComponent implements OnInit {

  svgUrl = environment.apiUrl + '/pattern.svg';

  constructor() {
  }

  ngOnInit() {
  }

}
