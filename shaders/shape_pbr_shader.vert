#define PANEL_MODE

#include "shape_shader_vertex_common"

uniform float uBumpScale;
uniform vec4 uBaseColor;
uniform float uMetallic;
uniform float uRoughness;
uniform float uReflectance;
uniform float uSpecularLevel;
uniform float uAmbientOcclusion;
uniform float uShadowStrength;
uniform vec3 uShadowColor;

in vec4 T;
out Vertex
{
	mat3 tangentToWorld;
	flat int cameraIndex;
	VertexAttrs attrs;
} oVert;

void main()
{
	TransformSettings transformSettings = loadTransformSettings();
	oVert.attrs = loadVertexAttrs(transformSettings);

	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(oVert.attrs.worldSpacePos, uvUnwrapCoord);


	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

	int cameraIndex = TDCameraIndex();
	oVert.cameraIndex = cameraIndex;
	oVert.attrs.color = TDInstanceColor(Cd);
	vec3 worldSpaceNorm = normalize(TDDeformNorm(N));
	vec4 worldSpaceNorm4 = vec4(worldSpaceNorm, 0);
	applyTransform(worldSpaceNorm4, transformSettings);
	worldSpaceNorm = worldSpaceNorm4.xyz;

	vec3 worldSpaceTangent = TDDeformNorm(T.xyz);
	worldSpaceTangent.xyz = normalize(worldSpaceTangent.xyz);
	// Create the matrix that will convert vectors and positions from
	// tangent space to world space
	// T.w contains the handedness of the tangent
	// It will be used to flip the bi-normal if needed
	oVert.tangentToWorld = TDCreateTBNMatrix(worldSpaceNorm, worldSpaceTangent, T.w);
//	scaleRotateTranslate(oVert.tangentToWorld, )

#else // TD_PICKING_ACTIVE

	// This will automatically write out the nessessary values
	// for this shader to work with picking.
	// See the documentation if you want to write custom values for picking.
	TDWritePickingValues();

#endif // TD_PICKING_ACTIVE
}
