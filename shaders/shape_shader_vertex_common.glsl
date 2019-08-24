// shape_shader_vertex_common.glsl

#include "shape_shader_common"

uniform sampler2D sColors;

uniform sampler2D sTransforms;
uniform sampler2D sTexParams;
uniform sampler2D sAttrs;

in vec3 centerPos;
in int shapeIndex;
in vec3 rotateAxis;

TexLayerAttrs loadTexLayerAttrs(in int shapeIndex, in VertexAttrs attrs, in int row) {
	return loadTexLayerAttrs(sTexParams, shapeIndex, attrs, row);
}

struct TransformSettings {
	vec3 localScale;
	vec3 localRotate;
	vec3 localTranslate;
	vec3 globalScale;
	vec3 globalRotate;
	vec3 globalTranslate;
};

TransformSettings loadTransformSettings() {
	TransformSettings settings;
	vec4 localScaleXYZUniform = texelFetch(sTransforms, ivec2(shapeIndex, 0), 0);
	settings.localScale = localScaleXYZUniform.xyz * localScaleXYZUniform.w;
	settings.localRotate = texelFetch(sTransforms, ivec2(shapeIndex, 1), 0).xyz;
	settings.localTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 2), 0).xyz;

	vec4 globalScaleXYZUniform = texelFetch(sTransforms, ivec2(shapeIndex, 3), 0);
	settings.globalScale = globalScaleXYZUniform.xyz * globalScaleXYZUniform.w;
	settings.globalRotate = texelFetch(sTransforms, ivec2(shapeIndex, 4), 0).xyz;
	settings.globalTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 5), 0).xyz;
	return settings;
}

void applyTransform(inout vec4 pos, in TransformSettings transformSettings) {
	scaleRotateTranslate(
		pos,
		transformSettings.globalScale,
		transformSettings.globalRotate,
		transformSettings.globalTranslate,
		vec3(0),
		rotateAxis);
	scaleRotateTranslate(
		pos,
		transformSettings.localScale,
		transformSettings.localRotate,
		transformSettings.localTranslate,
		centerPos,
		rotateAxis);
}

//void loadVertexAttrs(
//	inout VertexAttrs attrs,
//	in TransformSettings transformSettings) {
//	loadBasicVertexAttrs(
//		attrs,
//		shapeIndex,
//		sTexParams,
//		sColors,
//		sAttrs);
//
//	{ // Avoid duplicate variable defs
//		vec3 texcoord = TDInstanceTexCoord(uv[0]);
//		attrs.pathTexCoord.st = texcoord.st;
//	}
//
//	{ // Avoid duplicate variable defs
//		vec3 texcoord = TDInstanceTexCoord(uv[1]);
//		attrs.globalTexCoord = texcoord;
//	}
//
//	{ // Avoid duplicate variable defs
//		vec3 texcoord = TDInstanceTexCoord(uv[2]);
//		attrs.faceTexCoord = texcoord;
//	}
//
//
//	// First deform the vertex and normal
//	// TDDeform always returns values in world space
//	vec4 worldSpacePos = TDDeform(P);
//
//
//	if (!attrs.visible) {
//		worldSpacePos = vec4(-1000.0);
//	} else {
//		applyTransform(worldSpacePos, transformSettings);
//	}
//
//	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
//	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);
//
//	// This is here to ensure we only execute lighting etc. code
//	// when we need it. If picking is active we don't need lighting, so
//	// this entire block of code will be ommited from the compile.
//	// The TD_PICKING_ACTIVE define will be set automatically when
//	// picking is active.
//#ifndef TD_PICKING_ACTIVE
//
//	attrs.worldSpacePos.xyz = worldSpacePos.xyz;
////	attrs.color *= TDInstanceColor(Cd);
//
//#else // TD_PICKING_ACTIVE
//
//#endif // TD_PICKING_ACTIVE
//}

void loadVertexAttrs(inout VertexAttrs attrs, in TransformSettings transformSettings) {
//	VertexAttrs attrs;

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		attrs.pathTexCoord.st = texcoord.st;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[1]);
		attrs.globalTexCoord = texcoord;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[2]);
		attrs.faceTexCoord = texcoord;
	}

	attrs.shapeIndex = shapeIndex;
	attrs.color = texelFetch(sColors, ivec2(shapeIndex, 0), 0);
	attrs.visible = texelFetch(sAttrs, ivec2(shapeIndex, 0), 0).r > 0.5;

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);


	if (!attrs.visible) {
		worldSpacePos = vec4(-1000.0);
	} else {
		applyTransform(worldSpacePos, transformSettings);
	}

	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);

	#ifdef PATH_MODE
	attrs.pathTex = loadTexLayerAttrs(shapeIndex, attrs, 0);
	#endif
	#ifdef PANEL_MODE
	attrs.texLayer1 = loadTexLayerAttrs(shapeIndex, attrs, 0);
	attrs.texLayer2 = loadTexLayerAttrs(shapeIndex, attrs, 1);
	#endif

	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

	attrs.worldSpacePos.xyz = worldSpacePos.xyz;
//	attrs.color *= TDInstanceColor(Cd);

#else // TD_PICKING_ACTIVE

#endif // TD_PICKING_ACTIVE
}

VertexAttrs loadVertexAttrs() {
	TransformSettings transformSettings = loadTransformSettings();
	VertexAttrs attrs;
	loadVertexAttrs(attrs, transformSettings);
	return attrs;
}
