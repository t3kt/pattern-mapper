// shape_shader_pixel_common.glsl

#include "shape_shader_common"

uniform sampler2D sTexture1;
uniform sampler2D sTexture2;

vec3 getModifiedTexCoord(in VertexAttrs attrs, in TexLayerAttrs texAttrs) {
	vec3 coord = vec3(0.0);
	int uvMode = int(round(texAttrs.uvMode_textureIndex_compositeMode_level.x));
	switch (uvMode) {
		case UVMODE_GLOBAL: coord = attrs.globalTexCoord; break;
		case UVMODE_LOCAL: coord = attrs.faceTexCoord; break;
		case UVMODE_PATH: coord = vec3(attrs.texCoord0, 0.0); break;
	}
	coord -= texAttrs.pivot;
	coord = (vec4(coord, 0.0) * texAttrs.transform).xyz;
	coord += texAttrs.pivot;
	return coord;
}

vec4 getTextureColor(in VertexAttrs attrs, in TexLayerAttrs texAttrs) {
	vec3 coord = getModifiedTexCoord(attrs, texAttrs);
	int textureIndex = int(round(texAttrs.uvMode_textureIndex_compositeMode_level.y));
	if (textureIndex == 0) {
		return texture(sTexture1, coord.xy);
	} else if (textureIndex == 1) {
		return texture(sTexture1, coord.xy);
	}
	return vec4(0.0);
}


vec4 compositeColors(vec4 color1, vec4 color2, int compositeMode) {
	switch (compositeMode) {
		case COMP_ADD: return color1 + color2;
		case COMP_ATOP: return (color1.rgba * color2.a) + (color2.rgba * (1.0 - color1.a));
		case COMP_AVERAGE: return mix(color1, color2, 0.5);
		case COMP_DIFFERENCE: return vec4(abs(color1.rgb  - color2.rgb), color1.a);
		case COMP_INSIDE: return color1 * clamp(color2, 0.0, 1.0);
		case COMP_MAXIMUM: return max(color1, color2);
		case COMP_MINIMUM: return min(color1, color2);
		case COMP_MULTIPLY: return color1 * color2;
		case COMP_OUTSIDE: return color1 * (1.0 - color2.a);
		case COMP_OVER: return (color2 * (1.0 - color1.a)) + color1;
		case COMP_SCREEN: return 1.0 - ((1.0 - color1) * (1.0 - color2));
		case COMP_SUBTRACT: return color1 - color2;
		case COMP_UNDER: return (color1 * (1.0 - color2.a)) * color2;
	}
	return color1;
}

vec4 applyTexture(
	in vec4 baseColor,
	in VertexAttrs attrs,
	in TexLayerAttrs texAttrs) {

	float level = texAttrs.uvMode_textureIndex_compositeMode_level.w;
	if (level <= 0.0) {
		return baseColor;
	}

	vec4 texColor = getTextureColor(attrs, texAttrs);

	int compositeMode = int(round(texAttrs.uvMode_textureIndex_compositeMode_level.z));
	vec4 compedColor = compositeColors(baseColor, texColor, compositeMode);

	return mix(baseColor, compedColor, level);
}
