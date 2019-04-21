// shape_shader_vertex_common.glsl

#include "shape_shader_common"

uniform int uShapeCount;
uniform samplerBuffer bColors;
uniform samplerBuffer bLocalScales;
uniform samplerBuffer bLocalRotates;
uniform samplerBuffer bLocalTranslates;
uniform samplerBuffer bGlobalScales;
uniform samplerBuffer bGlobalRotates;
uniform samplerBuffer bGlobalTranslates;

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

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[1]);
		attrs.texCoord1.st = texcoord.st;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[2]);
		attrs.faceTexCoord.st = texcoord.st;
	}

	int shapeIndex = getShapeIndex(attrs.texCoord0.y);
	attrs.shapeIndex = shapeIndex;
	attrs.color = texelFetch(bColors, shapeIndex);

	vec3 localScale = texelFetch(bLocalScales, shapeIndex).xyz;
	vec3 localRotate = radians(texelFetch(bLocalRotates, shapeIndex).xyz);
	vec3 localTranslate = texelFetch(bLocalTranslates, shapeIndex).xyz;
	vec3 globalScale = texelFetch(bGlobalScales, shapeIndex).xyz;
	vec3 globalRotate = radians(texelFetch(bGlobalRotates, shapeIndex).xyz);
	vec3 globalTranslate = texelFetch(bGlobalTranslates, shapeIndex).xyz;

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);

	scaleRotateTranslate(
		worldSpacePos,
		localScale, localRotate, localTranslate,
		centerPos);
	scaleRotateTranslate(
		worldSpacePos,
		globalScale, globalRotate, globalTranslate,
		vec3(0));

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
