import { TestBed } from '@angular/core/testing';

import { PatternSettingsService } from './pattern-settings.service';

describe('PatternSettingsService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: PatternSettingsService = TestBed.get(PatternSettingsService);
    expect(service).toBeTruthy();
  });
});
