#define PANEL_MODE

#include "shape_shader_pixel_common"

uniform float uBumpScale;
uniform vec4 uBaseColor;
uniform float uMetallic;
uniform float uRoughness;
uniform float uReflectance;
uniform float uSpecularLevel;
uniform float uAmbientOcclusion;
uniform float uShadowStrength;
uniform vec3 uShadowColor;

uniform sampler2D sNormalMap;
uniform sampler2D sHeightMap;
uniform sampler2D sBaseColorMap;
uniform sampler2D sMetallicMap;
uniform sampler2D sRoughnessMap;
uniform sampler2D sAmbientOcclusionMap;

in Vertex
{
	mat3 tangentToWorld;
	flat int cameraIndex;
	VertexAttrs attrs;
} iVert;

// Output variable for the color
layout(location = 0) out vec4 oFragColor[TD_NUM_COLOR_BUFFERS];
void main()
{
	// This allows things such as order independent transparency
	// and Dual-Paraboloid rendering to work properly
	TDCheckDiscard();

	vec4 outcol = vec4(0.0, 0.0, 0.0, 0.0);
	vec3 diffuseSum = vec3(0.0, 0.0, 0.0);
	vec3 specularSum = vec3(0.0, 0.0, 0.0);

	vec2 texCoord0 = iVert.attrs.texCoord0.st;
	vec4 heightMapColor = texture(sHeightMap, texCoord0.st);
	vec4 normalMap = texture(sNormalMap, texCoord0.st);
	vec3 worldSpaceNorm = iVert.tangentToWorld[2];
	vec3 norm = (2.0 * (normalMap.xyz - 0.5)).xyz;
	norm.xy = norm.xy * uBumpScale;
	norm = iVert.tangentToWorld * norm;
	vec3 normal = normalize(norm);
	vec3 baseColor = uBaseColor.rgb;

	// 0.08 is the value for dielectric specular that
	// Substance Designer uses for it's top-end.
	float specularLevel = 0.08 * uSpecularLevel;
	float metallic = uMetallic;

	float roughness = uRoughness;

	float ambientOcclusion = uAmbientOcclusion;

	vec3 finalBaseColor = baseColor.rgb * iVert.attrs.color.rgb;

	vec4 baseColorMap = texture(sBaseColorMap, texCoord0.st);
	finalBaseColor *= baseColorMap.rgb;

	float mappingFactor = 1.0f;

	vec4 metallicMapColor = texture(sMetallicMap, texCoord0.st);
	mappingFactor = metallicMapColor.r;
	metallic *= mappingFactor;

	vec4 roughnessMapColor = texture(sRoughnessMap, texCoord0.st);
	mappingFactor = roughnessMapColor.r;
	roughness *= mappingFactor;

	vec4 ambientOcclusionMapColor = texture(sAmbientOcclusionMap, texCoord0.st);
	mappingFactor = ambientOcclusionMapColor.r;
	ambientOcclusion *= mappingFactor;

	// A roughness of exactly 0 is not allowed
	roughness = max(roughness, 0.0001);

	vec3 pbrDiffuseColor = finalBaseColor * (1.0 - metallic);
	vec3 pbrSpecularColor = mix(vec3(specularLevel), finalBaseColor, metallic);

	vec3 viewVec = normalize(uTDMats[iVert.cameraIndex].camInverse[3].xyz - iVert.attrs.worldSpacePos.xyz );

	// Flip the normals on backfaces
	// On most GPUs this function just return gl_FrontFacing.
	// However, some Intel GPUs on macOS have broken gl_FrontFacing behavior.
	// When one of those GPUs is detected, an alternative way
	// of determing front-facing is done using the position
	// and normal for this pixel.
	if (!TDFrontFacing(iVert.attrs.worldSpacePos.xyz, worldSpaceNorm.xyz))
	{
		normal = -normal;
	}

	// Your shader will be recompiled based on the number
	// of lights in your scene, so this continues to work
	// even if you change your lighting setup after the shader
	// has been exported from the Phong MAT
	for (int i = 0; i < TD_NUM_LIGHTS; i++)
	{
		vec3 diffuseContrib = vec3(0);
		vec3 specularContrib = vec3(0);
		TDLightingPBR(diffuseContrib,
			specularContrib,
			i,
			pbrDiffuseColor,
			pbrSpecularColor,
			iVert.attrs.worldSpacePos.xyz,
			normal,
			uShadowStrength, uShadowColor,
			viewVec,
			roughness
		);
		diffuseSum += diffuseContrib;
		specularSum += specularContrib;
	}

	// Environment lights
	for (int i = 0; i < TD_NUM_ENV_LIGHTS; i++)
	{
		vec3 diffuseContrib = vec3(0);
		vec3 specularContrib = vec3(0);
		TDEnvLightingPBR(diffuseContrib,
			specularContrib,
			i,
			pbrDiffuseColor,
			pbrSpecularColor,
			normal,
			viewVec,
			roughness,
			ambientOcclusion
		);
		diffuseSum += diffuseContrib;
		specularSum += specularContrib;
	}
	// Final Diffuse Contribution
	vec3 finalDiffuse = diffuseSum;
	outcol.rgb += finalDiffuse;

	// Final Specular Contribution
	vec3 finalSpecular = vec3(0.0);
	finalSpecular += specularSum;

	outcol.rgb += finalSpecular;


	// Apply fog, this does nothing if fog is disabled
	outcol = TDFog(outcol, iVert.attrs.worldSpacePos.xyz, iVert.cameraIndex);

	// Alpha Calculation
	float alpha = uBaseColor.a * iVert.attrs.color.a ;

	// Dithering, does nothing if dithering is disabled
	outcol = TDDither(outcol);

	outcol.rgb *= alpha;

	// Modern GL removed the implicit alpha test, so we need to apply
	// it manually here. This function does nothing if alpha test is disabled.
	TDAlphaTest(alpha);

	outcol.a = alpha;
	oFragColor[0] = TDOutputSwizzle(outcol);


	// TD_NUM_COLOR_BUFFERS will be set to the number of color buffers
	// active in the render. By default we want to output zero to every
	// buffer except the first one.
	for (int i = 1; i < TD_NUM_COLOR_BUFFERS; i++)
	{
		oFragColor[i] = vec4(0.0);
	}
}
