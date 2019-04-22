// shape_shader_vertex_common.glsl

#include "shape_shader_common"

uniform int uShapeCount;
uniform samplerBuffer bColors;

uniform sampler2D sTransforms;
uniform sampler2D sPanelTexParams;

in vec3 centerPos;

int getShapeIndex(float primOffset) {
	return int(primOffset * (uShapeCount-1));
}

VertexAttrs loadVertexAttrs() {
	VertexAttrs attrs;

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		attrs.texCoord0.st = texcoord.st;
	}
	int shapeIndex = getShapeIndex(attrs.texCoord0.y);

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[1]);
		attrs.globalTexCoord = texcoord;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[2]);
		attrs.faceTexCoord = texcoord;
	}

	attrs.shapeIndex = shapeIndex;
	attrs.color = texelFetch(bColors, shapeIndex);

	vec4 localOffsetAndLevel = texelFetch(sPanelTexParams, ivec2(shapeIndex, 0), 0);
	vec4 globalOffsetAndLevel = texelFetch(sPanelTexParams, ivec2(shapeIndex, 1), 0);

	attrs.faceTexCoord += localOffsetAndLevel.xyz;
	attrs.localTexLevel = localOffsetAndLevel.w;
	attrs.globalTexCoord += globalOffsetAndLevel.xyz;
	attrs.globalTexLevel = globalOffsetAndLevel.w;

	vec3 localScale = texelFetch(sTransforms, ivec2(shapeIndex, 0), 0).xyz;
	vec3 localRotate = texelFetch(sTransforms, ivec2(shapeIndex, 1), 0).xyz;
	vec3 localTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 2), 0).xyz;

	vec3 globalScale = texelFetch(sTransforms, ivec2(shapeIndex, 3), 0).xyz;
	vec3 globalRotate = texelFetch(sTransforms, ivec2(shapeIndex, 4), 0).xyz;
	vec3 globalTranslate = texelFetch(sTransforms, ivec2(shapeIndex, 5), 0).xyz;

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);

	scaleRotateTranslate(
		worldSpacePos,
		globalScale, globalRotate, globalTranslate,
		vec3(0));
	scaleRotateTranslate(
		worldSpacePos,
		localScale, localRotate, localTranslate,
		centerPos);

	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);

	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

	attrs.worldSpacePos.xyz = worldSpacePos.xyz;
	attrs.color = TDInstanceColor(Cd);

#else // TD_PICKING_ACTIVE

#endif // TD_PICKING_ACTIVE

	return attrs;
}
