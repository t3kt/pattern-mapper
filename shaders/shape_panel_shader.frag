#include "shape_shader_pixel_common"

uniform sampler2D sPointPositionalTexture;
uniform sampler2D sFaceTexture;

in Vertex
{
	VertexAttrs attrs;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();
	
	vec4 color = iVert.attrs.color;

//	vec4 positionalColor = texture(sPointPositionalTexture, iVert.attrs.texCoord1);
//	color = mix(color, positionalColor, positionalColor.a);

//	vec4 faceColor = texture(sFaceTexture, iVert.attrs.faceTexCoord);
//	color = mix(color, faceColor, faceColor.a);
	color.a *= iVert.attrs.alpha;

	TDAlphaTest(color.a);
	fragColor = TDOutputSwizzle(color);
}

