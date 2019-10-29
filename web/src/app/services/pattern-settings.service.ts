import { Injectable } from '@angular/core';
import {HttpClient} from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class PatternSettingsService {
  constructor(
    private http: HttpClient
  ) {}
}
