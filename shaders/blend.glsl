// Derived from https://github.com/jamieowen/glsl-blend

float blendAdd_1540259130(float base, float blend) {
	return min(base+blend,1.0);
}

vec3 blendAdd_1540259130(vec3 base, vec3 blend) {
	return min(base+blend,vec3(1.0));
}

vec3 blendAdd_1540259130(vec3 base, vec3 blend, float opacity) {
	return (blendAdd_1540259130(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendAverage_1604150559(vec3 base, vec3 blend) {
	return (base+blend)/2.0;
}

vec3 blendAverage_1604150559(vec3 base, vec3 blend, float opacity) {
	return (blendAverage_1604150559(base, blend) * opacity + base * (1.0 - opacity));
}

float blendColorBurn_1117569599(float base, float blend) {
	return (blend==0.0)?blend:max((1.0-((1.0-base)/blend)),0.0);
}

vec3 blendColorBurn_1117569599(vec3 base, vec3 blend) {
	return vec3(blendColorBurn_1117569599(base.r,blend.r),blendColorBurn_1117569599(base.g,blend.g),blendColorBurn_1117569599(base.b,blend.b));
}

vec3 blendColorBurn_1117569599(vec3 base, vec3 blend, float opacity) {
	return (blendColorBurn_1117569599(base, blend) * opacity + base * (1.0 - opacity));
}

float blendColorDodge_2281831123(float base, float blend) {
	return (blend==1.0)?blend:min(base/(1.0-blend),1.0);
}

vec3 blendColorDodge_2281831123(vec3 base, vec3 blend) {
	return vec3(blendColorDodge_2281831123(base.r,blend.r),blendColorDodge_2281831123(base.g,blend.g),blendColorDodge_2281831123(base.b,blend.b));
}

vec3 blendColorDodge_2281831123(vec3 base, vec3 blend, float opacity) {
	return (blendColorDodge_2281831123(base, blend) * opacity + base * (1.0 - opacity));
}

float blendDarken_1062606552(float base, float blend) {
	return min(blend,base);
}

vec3 blendDarken_1062606552(vec3 base, vec3 blend) {
	return vec3(blendDarken_1062606552(base.r,blend.r),blendDarken_1062606552(base.g,blend.g),blendDarken_1062606552(base.b,blend.b));
}

vec3 blendDarken_1062606552(vec3 base, vec3 blend, float opacity) {
	return (blendDarken_1062606552(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendDifference_1535977339(vec3 base, vec3 blend) {
	return abs(base-blend);
}

vec3 blendDifference_1535977339(vec3 base, vec3 blend, float opacity) {
	return (blendDifference_1535977339(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendExclusion_1460171947(vec3 base, vec3 blend) {
	return base+blend-2.0*base*blend;
}

vec3 blendExclusion_1460171947(vec3 base, vec3 blend, float opacity) {
	return (blendExclusion_1460171947(base, blend) * opacity + base * (1.0 - opacity));
}

float blendReflect_529295689(float base, float blend) {
	return (blend==1.0)?blend:min(base*base/(1.0-blend),1.0);
}

vec3 blendReflect_529295689(vec3 base, vec3 blend) {
	return vec3(blendReflect_529295689(base.r,blend.r),blendReflect_529295689(base.g,blend.g),blendReflect_529295689(base.b,blend.b));
}

vec3 blendReflect_529295689(vec3 base, vec3 blend, float opacity) {
	return (blendReflect_529295689(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendGlow_2645608689(vec3 base, vec3 blend) {
	return blendReflect_529295689(blend,base);
}

vec3 blendGlow_2645608689(vec3 base, vec3 blend, float opacity) {
	return (blendGlow_2645608689(base, blend) * opacity + base * (1.0 - opacity));
}

float blendOverlay_2315452051(float base, float blend) {
	return base<0.5?(2.0*base*blend):(1.0-2.0*(1.0-base)*(1.0-blend));
}

vec3 blendOverlay_2315452051(vec3 base, vec3 blend) {
	return vec3(blendOverlay_2315452051(base.r,blend.r),blendOverlay_2315452051(base.g,blend.g),blendOverlay_2315452051(base.b,blend.b));
}

vec3 blendOverlay_2315452051(vec3 base, vec3 blend, float opacity) {
	return (blendOverlay_2315452051(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendHardLight_782122993(vec3 base, vec3 blend) {
	return blendOverlay_2315452051(blend,base);
}

vec3 blendHardLight_782122993(vec3 base, vec3 blend, float opacity) {
	return (blendHardLight_782122993(base, blend) * opacity + base * (1.0 - opacity));
}

float blendVividLight_3517901130(float base, float blend) {
	return (blend<0.5)?blendColorBurn_1117569599(base,(2.0*blend)):blendColorDodge_2281831123(base,(2.0*(blend-0.5)));
}

vec3 blendVividLight_3517901130(vec3 base, vec3 blend) {
	return vec3(blendVividLight_3517901130(base.r,blend.r),blendVividLight_3517901130(base.g,blend.g),blendVividLight_3517901130(base.b,blend.b));
}

vec3 blendVividLight_3517901130(vec3 base, vec3 blend, float opacity) {
	return (blendVividLight_3517901130(base, blend) * opacity + base * (1.0 - opacity));
}

float blendHardMix_2658629798(float base, float blend) {
	return (blendVividLight_3517901130(base,blend)<0.5)?0.0:1.0;
}

vec3 blendHardMix_2658629798(vec3 base, vec3 blend) {
	return vec3(blendHardMix_2658629798(base.r,blend.r),blendHardMix_2658629798(base.g,blend.g),blendHardMix_2658629798(base.b,blend.b));
}

vec3 blendHardMix_2658629798(vec3 base, vec3 blend, float opacity) {
	return (blendHardMix_2658629798(base, blend) * opacity + base * (1.0 - opacity));
}

float blendLighten_421267681(float base, float blend) {
	return max(blend,base);
}

vec3 blendLighten_421267681(vec3 base, vec3 blend) {
	return vec3(blendLighten_421267681(base.r,blend.r),blendLighten_421267681(base.g,blend.g),blendLighten_421267681(base.b,blend.b));
}

vec3 blendLighten_421267681(vec3 base, vec3 blend, float opacity) {
	return (blendLighten_421267681(base, blend) * opacity + base * (1.0 - opacity));
}

float blendLinearBurn_870892966(float base, float blend) {
	// Note : Same implementation as BlendSubtractf
	return max(base+blend-1.0,0.0);
}

vec3 blendLinearBurn_870892966(vec3 base, vec3 blend) {
	// Note : Same implementation as BlendSubtract
	return max(base+blend-vec3(1.0),vec3(0.0));
}

vec3 blendLinearBurn_870892966(vec3 base, vec3 blend, float opacity) {
	return (blendLinearBurn_870892966(base, blend) * opacity + base * (1.0 - opacity));
}

float blendLinearDodge_3903765079(float base, float blend) {
	// Note : Same implementation as BlendAddf
	return min(base+blend,1.0);
}

vec3 blendLinearDodge_3903765079(vec3 base, vec3 blend) {
	// Note : Same implementation as BlendAdd
	return min(base+blend,vec3(1.0));
}

vec3 blendLinearDodge_3903765079(vec3 base, vec3 blend, float opacity) {
	return (blendLinearDodge_3903765079(base, blend) * opacity + base * (1.0 - opacity));
}

float blendLinearLight_2166047709(float base, float blend) {
	return blend<0.5?blendLinearBurn_870892966(base,(2.0*blend)):blendLinearDodge_3903765079(base,(2.0*(blend-0.5)));
}

vec3 blendLinearLight_2166047709(vec3 base, vec3 blend) {
	return vec3(blendLinearLight_2166047709(base.r,blend.r),blendLinearLight_2166047709(base.g,blend.g),blendLinearLight_2166047709(base.b,blend.b));
}

vec3 blendLinearLight_2166047709(vec3 base, vec3 blend, float opacity) {
	return (blendLinearLight_2166047709(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendMultiply_2976544439(vec3 base, vec3 blend) {
	return base*blend;
}

vec3 blendMultiply_2976544439(vec3 base, vec3 blend, float opacity) {
	return (blendMultiply_2976544439(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendNegation_3090588381(vec3 base, vec3 blend) {
	return vec3(1.0)-abs(vec3(1.0)-base-blend);
}

vec3 blendNegation_3090588381(vec3 base, vec3 blend, float opacity) {
	return (blendNegation_3090588381(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendNormal_2197045468(vec3 base, vec3 blend) {
	return blend;
}

vec3 blendNormal_2197045468(vec3 base, vec3 blend, float opacity) {
	return (blendNormal_2197045468(base, blend) * opacity + base * (1.0 - opacity));
}

vec3 blendPhoenix_4181093413(vec3 base, vec3 blend) {
	return min(base,blend)-max(base,blend)+vec3(1.0);
}

vec3 blendPhoenix_4181093413(vec3 base, vec3 blend, float opacity) {
	return (blendPhoenix_4181093413(base, blend) * opacity + base * (1.0 - opacity));
}

float blendPinLight_184046362(float base, float blend) {
	return (blend<0.5)?blendDarken_1062606552(base,(2.0*blend)):blendLighten_421267681(base,(2.0*(blend-0.5)));
}

vec3 blendPinLight_184046362(vec3 base, vec3 blend) {
	return vec3(blendPinLight_184046362(base.r,blend.r),blendPinLight_184046362(base.g,blend.g),blendPinLight_184046362(base.b,blend.b));
}

vec3 blendPinLight_184046362(vec3 base, vec3 blend, float opacity) {
	return (blendPinLight_184046362(base, blend) * opacity + base * (1.0 - opacity));
}

float blendScreen_2766173552(float base, float blend) {
	return 1.0-((1.0-base)*(1.0-blend));
}

vec3 blendScreen_2766173552(vec3 base, vec3 blend) {
	return vec3(blendScreen_2766173552(base.r,blend.r),blendScreen_2766173552(base.g,blend.g),blendScreen_2766173552(base.b,blend.b));
}

vec3 blendScreen_2766173552(vec3 base, vec3 blend, float opacity) {
	return (blendScreen_2766173552(base, blend) * opacity + base * (1.0 - opacity));
}

float blendSoftLight_208481169(float base, float blend) {
	return (blend<0.5)?(2.0*base*blend+base*base*(1.0-2.0*blend)):(sqrt(base)*(2.0*blend-1.0)+2.0*base*(1.0-blend));
}

vec3 blendSoftLight_208481169(vec3 base, vec3 blend) {
	return vec3(blendSoftLight_208481169(base.r,blend.r),blendSoftLight_208481169(base.g,blend.g),blendSoftLight_208481169(base.b,blend.b));
}

vec3 blendSoftLight_208481169(vec3 base, vec3 blend, float opacity) {
	return (blendSoftLight_208481169(base, blend) * opacity + base * (1.0 - opacity));
}

float blendSubtract_1921068617(float base, float blend) {
	return max(base+blend-1.0,0.0);
}

vec3 blendSubtract_1921068617(vec3 base, vec3 blend) {
	return max(base+blend-vec3(1.0),vec3(0.0));
}

vec3 blendSubtract_1921068617(vec3 base, vec3 blend, float opacity) {
	return (blendSubtract_1921068617(base, blend) * opacity + base * (1.0 - opacity));
}
